/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {Marker, Tooltip} from 'react-leaflet';
import Leaflet from 'leaflet';
import MarkerClusterGroup from 'react-leaflet-markercluster';
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
        id: PropTypes.number.isRequired
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
        /** 'actions' may be used by plugins */
        actions: PropTypes.objectOf(PropTypes.func).isRequired
    };

    static defaultProps = {
        rooms: [],
        clusterProps: {},
        hoveredRoomId: null
    };

    shouldComponentUpdate({rooms: newRooms, hoveredRoomId: newHovered}) {
        const {rooms: oldRooms, hoveredRoomId: oldHovered} = this.props;
        return !_.isEqual(oldRooms, newRooms) || newHovered !== oldHovered;
    }

    render() {
        const {rooms, clusterProps, hoveredRoomId} = this.props;

        if (!rooms.length) {
            return null;
        }

        return (
            <MarkerClusterGroup showCoverageOnHover={false}
                                iconCreateFunction={groupIconCreateFunction}
                                {...clusterProps}>
                {rooms.filter(({lat, lng}) => !!(lat && lng)).map(({id, name, lat, lng}) => {
                    return (
                        <MarkerWrapper key={id}
                                       id={id}
                                       position={[lat, lng]}
                                       icon={id === hoveredRoomId ? hoveredIcon : icon}
                                       highlight={id === hoveredRoomId}>
                            <Tooltip direction="top">
                                <span>{name}</span>
                            </Tooltip>
                        </MarkerWrapper>
                    );
                })}
            </MarkerClusterGroup>
        );
    }
}


export default connect(
    state => ({
        hoveredRoomId: mapSelectors.getHoveredRoom(state)
    })
)(MapMarkers);
