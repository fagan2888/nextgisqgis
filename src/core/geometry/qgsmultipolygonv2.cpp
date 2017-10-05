/***************************************************************************
                        qgsmultipolygonv2.cpp
  -------------------------------------------------------------------
Date                 : 28 Oct 2014
Copyright            : (C) 2014 by Marco Hugentobler
email                : marco.hugentobler at sourcepole dot com
 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#include "qgsmultipolygonv2.h"
#include "qgsapplication.h"
#include "qgsgeometryutils.h"
#include "qgssurfacev2.h"
#include "qgslinestringv2.h"
#include "qgspolygonv2.h"
#include "qgscurvepolygonv2.h"
#include "qgsmultilinestringv2.h"

QgsMultiPolygonV2::QgsMultiPolygonV2()
    : QgsMultiSurfaceV2()
{
  mWkbType = QgsWKBTypes::MultiPolygon;
}

QgsMultiPolygonV2 *QgsMultiPolygonV2::clone() const
{
  return new QgsMultiPolygonV2( *this );
}

bool QgsMultiPolygonV2::fromWkt( const QString& wkt )
{
  return fromCollectionWkt( wkt, QList<QgsAbstractGeometryV2*>() << new QgsPolygonV2, "Polygon" );
}

QDomElement QgsMultiPolygonV2::asGML2( QDomDocument& doc, int precision, const QString& ns ) const
{
  // GML2 does not support curves
  QDomElement elemMultiPolygon = doc.createElementNS( ns, "MultiPolygon" );
  Q_FOREACH ( const QgsAbstractGeometryV2 *geom, mGeometries )
  {
    if ( dynamic_cast<const QgsPolygonV2*>( geom ) )
    {
      QDomElement elemPolygonMember = doc.createElementNS( ns, "polygonMember" );
      elemPolygonMember.appendChild( geom->asGML2( doc, precision, ns ) );
      elemMultiPolygon.appendChild( elemPolygonMember );
    }
  }

  return elemMultiPolygon;
}

QDomElement QgsMultiPolygonV2::asGML3( QDomDocument& doc, int precision, const QString& ns ) const
{
  QDomElement elemMultiSurface = doc.createElementNS( ns, "MultiPolygon" );
  Q_FOREACH ( const QgsAbstractGeometryV2 *geom, mGeometries )
  {
    if ( dynamic_cast<const QgsPolygonV2*>( geom ) )
    {
      QDomElement elemSurfaceMember = doc.createElementNS( ns, "polygonMember" );
      elemSurfaceMember.appendChild( geom->asGML3( doc, precision, ns ) );
      elemMultiSurface.appendChild( elemSurfaceMember );
    }
  }

  return elemMultiSurface;
}

QString QgsMultiPolygonV2::asJSON( int precision ) const
{
  // GeoJSON does not support curves
  QString json = "{\"type\": \"MultiPolygon\", \"coordinates\": [";
  Q_FOREACH ( const QgsAbstractGeometryV2 *geom, mGeometries )
  {
    if ( dynamic_cast<const QgsPolygonV2*>( geom ) )
    {
      json += '[';

      const QgsPolygonV2* polygon = static_cast<const QgsPolygonV2*>( geom );

      QgsLineStringV2* exteriorLineString = polygon->exteriorRing()->curveToLine();
      QgsPointSequenceV2 exteriorPts;
      exteriorLineString->points( exteriorPts );
      json += QgsGeometryUtils::pointsToJSON( exteriorPts, precision ) + ", ";
      delete exteriorLineString;

      for ( int i = 0, n = polygon->numInteriorRings(); i < n; ++i )
      {
        QgsLineStringV2* interiorLineString = polygon->interiorRing( i )->curveToLine();
        QgsPointSequenceV2 interiorPts;
        interiorLineString->points( interiorPts );
        json += QgsGeometryUtils::pointsToJSON( interiorPts, precision ) + ", ";
        delete interiorLineString;
      }
      if ( json.endsWith( ", " ) )
      {
        json.chop( 2 ); // Remove last ", "
      }

      json += "], ";
    }
  }
  if ( json.endsWith( ", " ) )
  {
    json.chop( 2 ); // Remove last ", "
  }
  json += "] }";
  return json;
}

bool QgsMultiPolygonV2::addGeometry( QgsAbstractGeometryV2* g )
{
  if ( !dynamic_cast<QgsPolygonV2*>( g ) )
  {
    delete g;
    return false;
  }

  setZMTypeFromSubGeometry( g, QgsWKBTypes::MultiPolygon );
  return QgsGeometryCollectionV2::addGeometry( g );
}

QgsAbstractGeometryV2* QgsMultiPolygonV2::toCurveType() const
{
  QgsMultiSurfaceV2* multiSurface = new QgsMultiSurfaceV2();
  for ( int i = 0; i < mGeometries.size(); ++i )
  {
    multiSurface->addGeometry( mGeometries.at( i )->clone() );
  }
  return multiSurface;
}

QgsAbstractGeometryV2* QgsMultiPolygonV2::boundary() const
{
  QgsMultiLineStringV2* multiLine = new QgsMultiLineStringV2();
  for ( int i = 0; i < mGeometries.size(); ++i )
  {
    if ( QgsPolygonV2* polygon = dynamic_cast<QgsPolygonV2*>( mGeometries.at( i ) ) )
    {
      QgsAbstractGeometryV2* polygonBoundary = polygon->boundary();

      if ( QgsLineStringV2* lineStringBoundary = dynamic_cast< QgsLineStringV2* >( polygonBoundary ) )
      {
        multiLine->addGeometry( lineStringBoundary );
      }
      else if ( QgsMultiLineStringV2* multiLineStringBoundary = dynamic_cast< QgsMultiLineStringV2* >( polygonBoundary ) )
      {
        for ( int j = 0; j < multiLineStringBoundary->numGeometries(); ++j )
        {
          multiLine->addGeometry( multiLineStringBoundary->geometryN( j )->clone() );
        }
        delete multiLineStringBoundary;
      }
      else
      {
        delete polygonBoundary;
      }
    }
  }
  if ( multiLine->numGeometries() == 0 )
  {
    delete multiLine;
    return nullptr;
  }
  return multiLine;
}
