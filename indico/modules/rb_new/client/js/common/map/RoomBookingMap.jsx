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
import Leaflet from 'leaflet';
import {Map, TileLayer, Marker, Tooltip} from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-markercluster';
import {Overridable} from 'indico/react/util';
import {selectors as configSelectors} from '../config';
import * as mapSelectors from './selectors';

import 'leaflet/dist/leaflet.css';
import './RoomBookingMap.module.scss';


function groupIconCreateFunction(cluster) {
    const highlight = cluster.getAllChildMarkers().some(m => m.options.highlight);
    return Leaflet.divIcon({
        html: `<span>${cluster.getChildCount()}</span>`,
        className: `marker-cluster marker-cluster-small rb-map-cluster ${highlight ? 'highlight' : ''}`,
        iconSize: Leaflet.point(40, 40, true),
    });
}


function _MapMarkers({rooms, clusterProps, hoveredRoomId}) {
    const icon = Leaflet.divIcon({className: 'rb-map-marker', iconSize: [20, 20]});
    const hoveredIcon = Leaflet.divIcon({className: 'rb-map-marker highlight', iconSize: [20, 20]});
    const highlight = rooms.some(r => r.id === hoveredRoomId);

    return (
        !!rooms.length && (
            <MarkerClusterGroup showCoverageOnHover={false}
                                iconCreateFunction={groupIconCreateFunction}
                                // key is used here as a way to force a re-rendering
                                // of the MarkerClusterGroup
                                key={highlight}
                                {...clusterProps}>
                {rooms.filter(({lat, lng}) => !!(lat && lng)).map(({id, name, lat, lng}) => (
                    // we have to make the key depend on the highlighted state, otherwise
                    // the component won't properly refresh (for some strange reason)
                    <Marker key={id}
                            position={[lat, lng]}
                            icon={id === hoveredRoomId ? hoveredIcon : icon}
                            highlight={id === hoveredRoomId}>
                        <Tooltip direction="top">
                            <span>{name}</span>
                        </Tooltip>
                    </Marker>
                ))}
            </MarkerClusterGroup>
        )
    );
}

_MapMarkers.propTypes = {
    rooms: PropTypes.array,
    clusterProps: PropTypes.object,
    hoveredRoomId: PropTypes.number,
    /** 'actions' may be used by plugins */
    actions: PropTypes.objectOf(PropTypes.func).isRequired
};

_MapMarkers.defaultProps = {
    rooms: [],
    clusterProps: {},
    hoveredRoomId: null
};

const MapMarkers = connect(
    state => ({
        hoveredRoomId: mapSelectors.getHoveredRoom(state)
    })
)(_MapMarkers);


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
        markerComponent: PropTypes.func,
        actions: PropTypes.objectOf(PropTypes.func).isRequired
    };

    static defaultProps = {
        rooms: [],
        onLoad: () => {},
        children: null,
        tileServerURL: '',
        clusterProps: {},
        markerComponent: MapMarkers
    };

    componentDidMount() {
        const {onLoad} = this.props;
        onLoad();
    }

    render() {
        const {
            bounds, onMove, mapRef, rooms, children, tileServerURL, onTouch, clusterProps, actions,
            markerComponent: MarkerComponent
        } = this.props;

        const onMoveDebounced = _.debounce(onMove, 750);
        return !_.isEmpty(bounds) && (
            <div styleName="map-container">
                <Map ref={mapRef}
                     bounds={Object.values(bounds)}
                     onMoveend={onMoveDebounced}
                     onDragend={(e) => {
                         onTouch();
                         onMoveDebounced(e);
                     }}
                     onZoomend={(e) => {
                         onTouch();
                         onMoveDebounced(e);
                     }}>
                    <TileLayer attribution='© <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
                               minZoom="14"
                               maxZoom="20"
                               url={tileServerURL} />
                    <MarkerComponent rooms={rooms} clusterProps={clusterProps} actions={actions} />
                    {children}
                </Map>
            </div>
        );
    }
}


export default connect(
    state => ({
        tileServerURL: configSelectors.getTileServerURL(state)
    }),
)(Overridable.component('RoomBookingMap', RoomBookingMap));
