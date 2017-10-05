/***************************************************************************
  qgsmaplayerref.h
  --------------------------------------
  Date                 : January 2017
  Copyright            : (C) 2017 by Martin Dobias
  Email                : wonder dot sk at gmail dot com
 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#ifndef QGSMAPLAYERREF_H
#define QGSMAPLAYERREF_H

#include <QPointer>

#include "qgsmaplayer.h"
#include "qgsdataprovider.h"
#include "qgsmaplayerregistry.h"
#include "qgsvectorlayer.h"
#include "qgsvectordataprovider.h"
#include "qgsrasterlayer.h"
#include "qgsrasterdataprovider.h"

/** Internal structure to keep weak pointer to QgsMapLayer or layerId
 *  if the layer is not available yet.
 *  \note not available in Python bindings
 */
template<typename TYPE>
struct _LayerRef
{

  /**
   * Constructor for a layer reference from an existing map layer.
   * The layerId, source, name and provider members will automatically
   * be populated from this layer.
   */
  _LayerRef( TYPE *l = nullptr )
      : layer( l )
      , layerId( l ? l->id() : QString() )
      , source( l ? l->publicSource() : QString() )
      , name( l ? l->name() : QString() )
      , provider( layerProviderName( l ) )
  {}

  /**
   * Constructor for a weak layer reference, using a combination of layer ID,
   * \a name, public \a source and \a provider key.
   */
  _LayerRef( const QString &id, const QString &name = QString(), const QString &source = QString(), const QString &provider = QString() )
      : layer()
      , layerId( id )
      , source( source )
      , name( name )
      , provider( provider )
  {}

  /**
   * Sets the reference to point to a specified layer.
   */
  void setLayer( TYPE *l )
  {
    layer = l;
    layerId = l ? l->id() : QString();
    source = l ? l->publicSource() : QString();
    name = l ? l->name() : QString();
    provider = layerProviderName( l );
  }

  /**
   * Returns true if the layer reference is resolved and contains a reference to an existing
   * map layer.
   */
  operator bool() const
  {
    return static_cast< bool >( layer.data() );
  }

  /**
   * Forwards the to map layer.
   */
  TYPE *operator->() const
  {
    return layer.data();
  }

  /**
   * Returns a pointer to the layer, or nullptr if the reference has not yet been matched
   * to a layer.
   */
  TYPE *get() const
  {
    return layer.data();
  }

  //! Weak pointer to map layer
  QPointer<TYPE> layer;

  //! Original layer ID
  QString layerId;

  //! Weak reference to layer public source
  QString source;
  //! Weak reference to layer name
  QString name;
  //! Weak reference to layer provider
  QString provider;

  /**
   * Returns true if a layer matches the weak references to layer public source,
   * layer name and data provider contained in this layer reference.
   * \see resolveWeakly()
   */
  bool layerMatchesSource( QgsMapLayer *layer ) const
  {
    if ( layer->publicSource() != source ||
         layer->name() != name )
      return false;

    if ( layerProviderName( layer ) != provider )
      return false;

    return true;
  }

  /**
   * Resolves the map layer by attempting to find a layer with matching ID
   * within the map layer registry. If found, this reference will be updated to match
   * the found layer and the layer will be returned. If no matching layer is
   * found, a nullptr is returned.
   * \see resolveWeakly()
   */
  TYPE *resolve()
  {
    if ( !layerId.isEmpty() )
    {
      if ( TYPE *l = qobject_cast<TYPE *>( QgsMapLayerRegistry::instance()->mapLayer( layerId ) ) )
      {
        setLayer( l );
        return l;
      }
    }
    return nullptr;
  }

  /**
   * Resolves the map layer by attempting to find a matching layer
   * in the map layer registry using a weak match.
   *
   * First, the layer is attempted to match to registry layers using the
   * layer's ID (calling this method implicitly calls resolve()).
   *
   * Failing a match by layer ID, the layer will be matched by using
   * the weak references to layer public source, layer name and data
   * provider contained in this layer reference.
   *
   * If a matching layer is found, this reference will be updated to match
   * the found layer and the layer will be returned. If no matching layer is
   * found, a nullptr is returned.
   * \see resolve()
   * \see layerMatchesSource()
   */
  TYPE *resolveWeakly()
  {
    // first try matching by layer ID
    if ( resolve() )
      return layer;

    if ( !name.isEmpty() )
    {
      Q_FOREACH ( QgsMapLayer *l, QgsMapLayerRegistry::instance()->mapLayersByName( name ) )
      {
        if ( TYPE *tl = qobject_cast< TYPE *>( l ) )
        {
          if ( layerMatchesSource( tl ) )
          {
            setLayer( tl );
            return tl;
          }
        }
      }
    }
    return nullptr;
  }

private:

  static QString layerProviderName( const QgsMapLayer *layer )
  {
    if ( !layer )
      return QString();

    switch ( layer->type() )
    {
      case QgsMapLayer::VectorLayer:
      {
        const QgsVectorLayer *vl = qobject_cast< const QgsVectorLayer *>( layer );
        return vl->dataProvider()->name();
      }

      case QgsMapLayer::RasterLayer:
      {
        const QgsRasterLayer *rl = qobject_cast< const QgsRasterLayer *>( layer );
        return rl->dataProvider()->name();
      }
      case QgsMapLayer::PluginLayer:
        return QString();
    }
    return QString();

  }
};

typedef _LayerRef<QgsMapLayer> QgsMapLayerRef;

#endif // QGSMAPLAYERREF_H
