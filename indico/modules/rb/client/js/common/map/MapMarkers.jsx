// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import Leaflet from 'leaflet';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Marker, Tooltip} from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-markercluster';
import {connect} from 'react-redux';

import * as mapSelectors from './selectors';

function groupIconCreateFunction(cluster) {
  const highlight = cluster.getAllChildMarkers().some(m => m.options.highlight);
  return Leaflet.divIcon({
    html: `<span>${cluster.getChildCount()}</span>`,
    className: `marker-cluster marker-cluster-small rb-map-cluster ${highlight ? 'highlight' : ''}`,
    iconSize: Leaflet.point(40, 40, true),
  });
}

const icon = Leaflet.divIcon({className: 'rb-map-marker', iconSize: [20, 20]});
const hoveredIcon = Leaflet.divIcon({className: 'rb-map-marker highlight', iconSize: [20, 20]});

/**
 * This wrapper is used to avoid re-rendering of <Marker> on every parent
 * cycle. By adding MarkerWrapper, we gain control of that through
 * shouldComponentUpdate(...)
 */
class MarkerWrapper extends React.Component {
  static propTypes = {
    highlight: PropTypes.bool.isRequired,
    id: PropTypes.number.isRequired,
  };

  shouldComponentUpdate({highlight: newHighlight}) {
    const {highlight: oldHighlight} = this.props;
    return newHighlight !== oldHighlight;
  }

  render() {
    const {id, highlight} = this.props;
    // HACK: 'highlight' is added since otherwise the marker is not re-rendered
    // on the leaflet side (not sure why).
    return <Marker key={`${id}-${highlight}`} {...this.props} />;
  }
}

/**
 * Wrapper around <MarkerClusterGroup /> that groups the room markers
 * shown on the map and handles the highlighting of the hovered room.
 */
class MapMarkers extends React.Component {
  static propTypes = {
    rooms: PropTypes.array,
    clusterProps: PropTypes.object,
    hoveredRoomId: PropTypes.number,
    onRoomClick: PropTypes.func.isRequired,
    /** 'actions' may be used by plugins */
    actions: PropTypes.objectOf(PropTypes.func).isRequired,
  };

  static defaultProps = {
    rooms: [],
    clusterProps: {},
    hoveredRoomId: null,
  };

  shouldComponentUpdate({rooms: newRooms, hoveredRoomId: newHovered}) {
    const {rooms: oldRooms, hoveredRoomId: oldHovered} = this.props;
    return !_.isEqual(oldRooms, newRooms) || newHovered !== oldHovered;
  }

  render() {
    const {rooms, clusterProps, hoveredRoomId, onRoomClick} = this.props;

    if (!rooms.length) {
      return null;
    }

    return (
      <MarkerClusterGroup
        showCoverageOnHover={false}
        iconCreateFunction={groupIconCreateFunction}
        {...clusterProps}
      >
        {rooms
          .filter(({lat, lng}) => !!(lat && lng))
          .map(room => (
            <MarkerWrapper
              key={room.id}
              id={room.id}
              position={[room.lat, room.lng]}
              icon={room.id === hoveredRoomId ? hoveredIcon : icon}
              highlight={room.id === hoveredRoomId}
              onClick={() => onRoomClick(room)}
            >
              <Tooltip direction="top">
                <span>{room.name}</span>
              </Tooltip>
            </MarkerWrapper>
          ))}
      </MarkerClusterGroup>
    );
  }
}

export default connect(state => ({
  hoveredRoomId: mapSelectors.getHoveredRoom(state),
}))(MapMarkers);
