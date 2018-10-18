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
import ReactDOM from 'react-dom';
import {connect} from 'react-redux';
import Leaflet from 'leaflet';
import {Map, TileLayer, MapControl, Marker, Tooltip} from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-markercluster';
import {selectors as configSelectors} from '../config';

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
        tileServerURL: PropTypes.string
    };

    static defaultProps = {
        rooms: [],
        onLoad: () => {},
        children: null,
        tileServerURL: ''
    };

    componentDidMount() {
        const {onLoad} = this.props;
        onLoad();
    }

    render() {
        const {bounds, onMove, mapRef, rooms, children, tileServerURL, onTouch} = this.props;
        Leaflet.Marker.prototype.options.icon = Leaflet.divIcon({className: 'rb-map-marker', iconSize: [20, 20]});

        const markers = !!rooms.length && (
            <MarkerClusterGroup showCoverageOnHover={false}>
                {rooms.filter(({lat, lng}) => !!(lat && lng)).map(({id, name, lat, lng}) => (
                    <Marker key={id} position={[lat, lng]}>
                        <Tooltip direction="top">
                            <span>{name}</span>
                        </Tooltip>
                    </Marker>
                ))}
            </MarkerClusterGroup>
        );

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
                    {markers}
                    {children}
                </Map>
            </div>
        );
    }
}


export class RoomBookingMapControl extends MapControl {
    static propTypes = {
        position: PropTypes.string.isRequired,
        classes: PropTypes.string,
    };

    static defaultProps = {
        classes: '',
    };

    componentWillMount() {
        const {position, classes} = this.props;
        const mapControl = Leaflet.control({position});
        mapControl.onAdd = () => {
            const div = Leaflet.DomUtil.create('div', classes);
            Leaflet.DomEvent.disableClickPropagation(div);
            Leaflet.DomEvent.disableScrollPropagation(div);
            return div;
        };
        this.leafletElement = mapControl;
    }

    componentDidMount() {
        super.componentDidMount();
        this.renderControl();
    }

    componentDidUpdate(prevProps) {
        const {classes} = this.props;
        super.componentDidUpdate(prevProps);
        this.renderControl();
        if (classes) {
            this.leafletElement.getContainer().classList.add(...classes.trim().split(' '));
        }
    }

    componentWillUnmount() {
        ReactDOM.unmountComponentAtNode(this.leafletElement.getContainer());
    }

    renderControl() {
        const container = this.leafletElement.getContainer();
        ReactDOM.render(React.Children.only(this.props.children), container);
    }
}

export default connect(
    state => ({
        tileServerURL: configSelectors.getTileServerURL(state),
    }),
)(RoomBookingMap);
