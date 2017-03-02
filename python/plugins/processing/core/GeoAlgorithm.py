# -*- coding: utf-8 -*-

"""
***************************************************************************
    GeoAlgorithmExecutionException.py
    ---------------------
    Date                 : August 2012
    Copyright            : (C) 2012 by Victor Olaya
    Email                : volayaf at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""


__author__ = 'Victor Olaya'
__date__ = 'August 2012'
__copyright__ = '(C) 2012, Victor Olaya'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os.path
import traceback
import subprocess
import copy

from PyQt4.QtGui import QIcon
from PyQt4.QtCore import QCoreApplication, QSettings
from qgis.core import QGis, QgsRasterFileWriter

from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import ParameterRaster, ParameterVector, ParameterMultipleInput, ParameterTable, Parameter
from processing.core.outputs import OutputVector, OutputRaster, OutputTable, OutputHTML, Output
from processing.algs.gdal.GdalUtils import GdalUtils
from processing.tools import dataobjects, vector
from processing.tools.system import setTempOutput
from processing.algs.help import shortHelp


class GeoAlgorithm:

    def __init__(self):
        self._icon = QIcon(os.path.dirname(__file__) + '/../images/alg.png')
        # Parameters needed by the algorithm
        self.parameters = list()

        # Outputs generated by the algorithm
        self.outputs = list()

        # Name and group for normal toolbox display
        self.name, self.i18n_name = '', ''
        self.group, self.i18n_group = '', ''

        # The crs taken from input layers (if possible), and used when
        # loading output layers
        self.crs = None

        # Change any of the following if your algorithm should not
        # appear in the toolbox or modeler
        self.showInToolbox = True
        self.showInModeler = True
        #if true, will show only loaded layers in parameters dialog.
        #Also, if True, the algorithm does not run on the modeler
        #or batch ptocessing interface
        self.allowOnlyOpenedLayers = False

        # False if it should not be run a a batch process
        self.canRunInBatchMode = True

        # To be set by the provider when it loads the algorithm
        self.provider = None

        # If the algorithm is run as part of a model, the parent model
        # can be set in this variable, to allow for customized
        # behaviour, in case some operations should be run differently
        # when running as part of a model
        self.model = None

        self.defineCharacteristics()

    def getCopy(self):
        """Returns a new instance of this algorithm, ready to be used
        for being executed.
        """
        newone = copy.copy(self)
        newone.parameters = copy.deepcopy(self.parameters)
        newone.outputs = copy.deepcopy(self.outputs)
        return newone

    # methods to overwrite when creating a custom geoalgorithm

    def getIcon(self):
        return self._icon

    @staticmethod
    def getDefaultIcon():
        return GeoAlgorithm._icon

    def _formatHelp(self, text):
        return "<h2>%s</h2>%s" % (self.name, "".join(["<p>%s</p>" % s for s in text.split("\n")]))

    def help(self):
        return False, None

    def shortHelp(self):
        text = shortHelp.get(self.commandLineName(), None)
        if text is not None:
            text = self._formatHelp(text)
        return text

    def processAlgorithm(self, progress):
        """Here goes the algorithm itself.

        There is no return value from this method.
        A GeoAlgorithmExecutionException should be raised in case
        something goes wrong.
        """
        pass

    def defineCharacteristics(self):
        """Here is where the parameters and outputs should be defined.
        """
        pass

    def getCustomParametersDialog(self):
        """If the algorithm has a custom parameters dialog, it should
        be returned here, ready to be executed.
        """
        return None

    def getCustomModelerParametersDialog(self, modelAlg, algName=None):
        """If the algorithm has a custom parameters dialog when called
        from the modeler, it should be returned here, ready to be
        executed.
        """
        return None

    def getParameterDescriptions(self):
        """Returns a dict with param names as keys and detailed
        descriptions of each param as value. These descriptions are
        used as tool tips in the parameters dialog.

        If a description does not exist, the parameter's
        human-readable name is used.
        """
        descs = {}
        return descs

    def checkBeforeOpeningParametersDialog(self):
        """If there is any check to perform before the parameters
        dialog is opened, it should be done here.

        This method returns an error message string if there is any
        problem (for instance, an external app not configured yet),
        or None if the parameters dialog can be opened.

        Note that this check should also be done in the
        processAlgorithm method, since algorithms can be called without
        opening the parameters dialog.
        """
        return None

    def checkParameterValuesBeforeExecuting(self):
        """If there is any check to do before launching the execution
        of the algorithm, it should be done here.

        If values are not correct, a message should be returned
        explaining the problem.

        This check is called from the parameters dialog, and also when
        calling from the console.
        """
        return None

    # =========================================================

    def execute(self, progress=None, model=None):
        """The method to use to call a processing algorithm.

        Although the body of the algorithm is in processAlgorithm(),
        it should be called using this method, since it performs
        some additional operations.

        Raises a GeoAlgorithmExecutionException in case anything goes
        wrong.
        """
        self.model = model
        try:
            self.setOutputCRS()
            self.resolveTemporaryOutputs()
            self.resolveDataObjects()
            self.checkOutputFileExtensions()
            self.runPreExecutionScript(progress)
            self.processAlgorithm(progress)
            progress.setPercentage(100)
            self.convertUnsupportedFormats(progress)
            self.runPostExecutionScript(progress)
        except GeoAlgorithmExecutionException as gaee:
            ProcessingLog.addToLog(ProcessingLog.LOG_ERROR, gaee.msg)
            raise gaee
        except Exception as e:
            # If something goes wrong and is not caught in the
            # algorithm, we catch it here and wrap it
            lines = [self.tr('Uncaught error while executing algorithm')]
            lines.append(traceback.format_exc())
            ProcessingLog.addToLog(ProcessingLog.LOG_ERROR, lines)
            try:
                message = unicode(e)
            except UnicodeDecodeError:
                # Try with the 'replace' mode (requires e.message instead of e!)
                message = unicode(e.message, 'utf-8', 'replace')
            raise GeoAlgorithmExecutionException(
                message + self.tr(' \nSee log for more details'))

    def _checkParameterValuesBeforeExecuting(self):
        for param in self.parameters:
            if isinstance(param, (ParameterRaster, ParameterVector,
                                  ParameterMultipleInput)):
                if param.value:
                    if isinstance(param, ParameterMultipleInput):
                        inputlayers = param.value.split(';')
                    else:
                        inputlayers = [param.value]
                    for inputlayer in inputlayers:
                        obj = dataobjects.getObject(inputlayer)
                        if obj is None:
                            return "Wrong parameter value: " + param.value
        return self.checkParameterValuesBeforeExecuting()

    def runPostExecutionScript(self, progress):
        scriptFile = ProcessingConfig.getSetting(
            ProcessingConfig.POST_EXECUTION_SCRIPT)
        self.runHookScript(scriptFile, progress)

    def runPreExecutionScript(self, progress):
        scriptFile = ProcessingConfig.getSetting(
            ProcessingConfig.PRE_EXECUTION_SCRIPT)
        self.runHookScript(scriptFile, progress)

    def runHookScript(self, filename, progress):
        if filename is None or not os.path.exists(filename):
            return
        try:
            script = 'import processing\n'
            ns = {}
            ns['progress'] = progress
            ns['alg'] = self
            f = open(filename)
            lines = f.readlines()
            for line in lines:
                script += line
            exec(script, ns)
        except:
            # A wrong script should not cause problems, so we swallow
            # all exceptions
            pass

    def convertUnsupportedFormats(self, progress):
        i = 0
        progress.setText(self.tr('Converting outputs'))
        for out in self.outputs:
            if isinstance(out, OutputVector):
                if out.compatible is not None:
                    layer = dataobjects.getObjectFromUri(out.compatible)
                    if layer is None:
                        # For the case of memory layer, if the
                        # getCompatible method has been called
                        continue
                    provider = layer.dataProvider()
                    writer = out.getVectorWriter(
                        provider.fields(),
                        provider.geometryType(), layer.crs()
                    )
                    features = vector.features(layer)
                    for feature in features:
                        writer.addFeature(feature)
            elif isinstance(out, OutputRaster):
                if out.compatible is not None:
                    layer = dataobjects.getObjectFromUri(out.compatible)
                    format = self.getFormatShortNameFromFilename(out.value)
                    orgFile = out.compatible
                    destFile = out.value
                    crsid = layer.crs().authid()
                    settings = QSettings()
                    path = unicode(settings.value('/GdalTools/gdalPath', ''))
                    envval = unicode(os.getenv('PATH'))
                    if not path.lower() in envval.lower().split(os.pathsep):
                        envval += '%s%s' % (os.pathsep, path)
                        os.putenv('PATH', envval)
                    command = 'gdal_translate -of %s -a_srs %s %s %s' % (format, crsid, orgFile, destFile)
                    if os.name == 'nt':
                        command = command.split(" ")
                    else:
                        command = [command]
                    proc = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stdin=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=False,
                    )
                    proc.communicate()

            elif isinstance(out, OutputTable):
                if out.compatible is not None:
                    layer = dataobjects.getObjectFromUri(out.compatible)
                    provider = layer.dataProvider()
                    writer = out.getTableWriter(provider.fields())
                    features = vector.features(layer)
                    for feature in features:
                        writer.addRecord(feature)
            progress.setPercentage(100 * i / float(len(self.outputs)))

    def getFormatShortNameFromFilename(self, filename):
        ext = filename[filename.rfind('.') + 1:]
        supported = GdalUtils.getSupportedRasters()
        for name in supported.keys():
            exts = supported[name]
            if ext in exts:
                return name
        return 'GTiff'

    def checkOutputFileExtensions(self):
        """Checks if the values of outputs are correct and have one of
        the supported output extensions.

        If not, it adds the first one of the supported extensions, which
        is assumed to be the default one.
        """
        for out in self.outputs:
            if not out.hidden and out.value is not None:
                if not os.path.isabs(out.value):
                    continue
                if isinstance(out, OutputRaster):
                    exts = \
                        dataobjects.getSupportedOutputRasterLayerExtensions()
                elif isinstance(out, OutputVector):
                    exts = \
                        dataobjects.getSupportedOutputVectorLayerExtensions()
                elif isinstance(out, OutputTable):
                    exts = dataobjects.getSupportedOutputTableExtensions()
                elif isinstance(out, OutputHTML):
                    exts = ['html', 'htm']
                else:
                    continue
                idx = out.value.rfind('.')
                if idx == -1:
                    out.value = out.value + '.' + exts[0]
                else:
                    ext = out.value[idx + 1:]
                    if ext not in exts:
                        out.value = out.value + '.' + exts[0]

    def resolveTemporaryOutputs(self):
        """Sets temporary outputs (output.value = None) with a
        temporary file instead.
        """
        for out in self.outputs:
            if not out.hidden and out.value is None:
                setTempOutput(out, self)

    def setOutputCRS(self):
        layers = dataobjects.getAllLayers()
        for param in self.parameters:
            if isinstance(param, (ParameterRaster, ParameterVector, ParameterMultipleInput)):
                if param.value:
                    if isinstance(param, ParameterMultipleInput):
                        inputlayers = param.value.split(';')
                    else:
                        inputlayers = [param.value]
                    for inputlayer in inputlayers:
                        for layer in layers:
                            if layer.source() == inputlayer:
                                self.crs = layer.crs()
                                return
                        p = dataobjects.getObjectFromUri(inputlayer)
                        if p is not None:
                            self.crs = p.crs()
                            p = None
                            return
        try:
            from qgis.utils import iface
            if iface is not None:
                self.crs = iface.mapCanvas().mapSettings().destinationCrs()
        except:
            pass

    def resolveDataObjects(self):
        layers = dataobjects.getAllLayers()
        for param in self.parameters:
            if isinstance(param, (ParameterRaster, ParameterVector, ParameterTable,
                                  ParameterMultipleInput)):
                if param.value:
                    if isinstance(param, ParameterMultipleInput):
                        inputlayers = param.value.split(';')
                    else:
                        inputlayers = [param.value]
                    for i, inputlayer in enumerate(inputlayers):
                        for layer in layers:
                            if layer.name() == inputlayer:
                                inputlayers[i] = layer.source()
                                break
                    param.setValue(";".join(inputlayers))

    def checkInputCRS(self):
        """It checks that all input layers use the same CRS. If so,
        returns True. False otherwise.
        """
        crsList = []
        for param in self.parameters:
            if isinstance(param, (ParameterRaster, ParameterVector, ParameterMultipleInput)):
                if param.value:
                    if isinstance(param, ParameterMultipleInput):
                        layers = param.value.split(';')
                    else:
                        layers = [param.value]
                    for item in layers:
                        crs = dataobjects.getObject(item).crs()
                        if crs not in crsList:
                            crsList.append(crs)
        return len(crsList) < 2

    def addOutput(self, output):
        # TODO: check that name does not exist
        if isinstance(output, Output):
            self.outputs.append(output)

    def addParameter(self, param):
        # TODO: check that name does not exist
        if isinstance(param, Parameter):
            self.parameters.append(param)

    def setParameterValue(self, paramName, value):
        for param in self.parameters:
            if param.name == paramName:
                return param.setValue(value)

    def setOutputValue(self, outputName, value):
        for out in self.outputs:
            if out.name == outputName:
                out.setValue(value)

    def getVisibleOutputsCount(self):
        """Returns the number of non-hidden outputs.
        """
        i = 0
        for out in self.outputs:
            if not out.hidden:
                i += 1
        return i

    def getVisibleParametersCount(self):
        """Returns the number of non-hidden parameters.
        """
        i = 0
        for param in self.parameters:
            if not param.hidden:
                i += 1
        return i

    def getHTMLOutputsCount(self):
        """Returns the number of HTML outputs.
        """
        i = 0
        for out in self.outputs:
            if isinstance(out, OutputHTML):
                i += 1
        return i

    def getOutputValuesAsDictionary(self):
        d = {}
        for out in self.outputs:
            d[out.name] = out.value
        return d

    def __str__(self):
        s = 'ALGORITHM: ' + self.name + '\n'
        for param in self.parameters:
            s += '\t' + unicode(param) + '\n'
        for out in self.outputs:
            s += '\t' + unicode(out) + '\n'
        s += '\n'
        return s

    def commandLineName(self):
        name = self.provider.getName().lower() + ':' + self.name.lower()
        validChars = \
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:'
        name = ''.join(c for c in name if c in validChars)
        return name

    def removeOutputFromName(self, name):
        for out in self.outputs:
            if out.name == name:
                self.outputs.remove(out)

    def getOutputFromName(self, name):
        for out in self.outputs:
            if out.name == name:
                return out

    def getParameterFromName(self, name):
        for param in self.parameters:
            if param.name == name:
                return param

    def getParameterValue(self, name):
        for param in self.parameters:
            if param.name == name:
                return param.value
        return None

    def getOutputValue(self, name):
        for out in self.outputs:
            if out.name == name:
                return out.value
        return None

    def getAsCommand(self):
        """Returns the command that would run this same algorithm from
        the console.

        Should return None if the algorithm cannot be run from the
        console.
        """

        s = 'processing.runalg("' + self.commandLineName() + '",'
        for param in self.parameters:
            s += param.getValueAsCommandLineParameter() + ','
        for out in self.outputs:
            if not out.hidden:
                s += out.getValueAsCommandLineParameter() + ','
        s = s[:-1] + ')'
        return s

    def tr(self, string, context=''):
        if context == '':
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)

    def trAlgorithm(self, string, context=''):
        if context == '':
            context = self.__class__.__name__
        return string, QCoreApplication.translate(context, string)
