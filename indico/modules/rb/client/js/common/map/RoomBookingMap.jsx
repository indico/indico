// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {Map, TileLayer} from 'react-leaflet';
import Overridable from 'react-overridable';
import {selectors as configSelectors} from '../config';
import MapMarkers from './MapMarkers';

import 'leaflet/dist/leaflet.css';
import './RoomBookingMap.module.scss';

class RoomBookingMap extends React.Component {
  static propTypes = {
    bounds: PropTypes.object.isRequired,
    onMove: PropTypes.func.isRequired,
    onTouch: PropTypes.func.isRequired,
    mapRef: PropTypes.object.isRequired,
    rooms: PropTypes.array,
    onLoad: PropTypes.func,
    children: PropTypes.node,
    tileServerURL: PropTypes.string,
    clusterProps: PropTypes.object,
    markerComponent: PropTypes.elementType,
    onRoomClick: PropTypes.func.isRequired,
    actions: PropTypes.objectOf(PropTypes.func).isRequired,
  };

  static defaultProps = {
    rooms: [],
    onLoad: () => {},
    children: null,
    tileServerURL: '',
    clusterProps: {},
    markerComponent: MapMarkers,
  };

  componentDidMount() {
    const {onLoad} = this.props;
    onLoad();
  }

  render() {
    const {
      bounds,
      onMove,
      mapRef,
      rooms,
      children,
      tileServerURL,
      onTouch,
      clusterProps,
      onRoomClick,
      actions,
      markerComponent: MarkerComponent,
    } = this.props;

    const onMoveDebounced = _.debounce(onMove, 750);
    return (
      !_.isEmpty(bounds) && (
        <div styleName="map-container">
          <Map
            ref={mapRef}
            bounds={Object.values(bounds)}
            onMoveend={onMoveDebounced}
            onDragend={e => {
              onTouch();
              onMoveDebounced(e);
            }}
            onZoomend={e => {
              onTouch();
              onMoveDebounced(e);
            }}
          >
            <TileLayer
              attribution='© <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
              minZoom="14"
              maxZoom="20"
              url={tileServerURL}
            />
            <MarkerComponent
              rooms={rooms}
              clusterProps={clusterProps}
              actions={actions}
              onRoomClick={onRoomClick}
            />
            {children}
          </Map>
        </div>
      )
    );
  }
}

export default connect(state => ({
  tileServerURL: configSelectors.getTileServerURL(state),
}))(Overridable.component('RoomBookingMap', RoomBookingMap));
