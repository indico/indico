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

import React from 'react';
import PropTypes from 'prop-types';
import {Dimmer, Loader} from 'semantic-ui-react';

import {getAspectBounds, getMapBounds} from '../util';
import RoomBookingMap from './RoomBookingMap';

import './MapController.module.scss';


export default class MapController extends React.Component {
    static propTypes = {
        map: PropTypes.shape({
            bounds: PropTypes.object,
        }).isRequired,
        filterBounds: PropTypes.object,
        fetchMapDefaultAspects: PropTypes.func.isRequired,
        fetchRooms: PropTypes.func.isRequired,
        toggleMapSearch: PropTypes.func.isRequired,
        updateLocation: PropTypes.func.isRequired
    };

    static defaultProps = {
        filterBounds: null
    };

    static getDerivedStateFromProps({filterBounds, map: {bounds}}) {
        return {
            aspectBounds: filterBounds || bounds
        };
    }

    constructor(props) {
        super(props);
        this.map = React.createRef();

        this.state = {
            loading: true,
            aspectsLoaded: false
        };

        this.loadAspects();
    }

    async componentDidMount() {
        const {fetchRooms} = this.props;
        fetchRooms();
    }

    async loadAspects() {
        const {aspectBounds, fetchMapDefaultAspects} = this.props;
        if (!aspectBounds) {
            await fetchMapDefaultAspects();
        }
        this.setState({
            aspectsLoaded: true
        });
    }

    onMapLoad = async () => {
        const {filterBounds, toggleMapSearch} = this.props;
        this.updateToMapBounds();
        toggleMapSearch(!_.isEmpty(filterBounds), filterBounds);
        this.setState({
            loading: false
        });
    };

    onMove = (e) => {
        const {updateLocation, map: {search}} = this.props;
        updateLocation(getMapBounds(e.target), search);
    };

    onChangeAspect(aspectIdx) {
        const {map: {aspects}} = this.props;
        this.setState({aspectBounds: getAspectBounds(aspects[aspectIdx])}, this.updateToMapBounds);
    }

    updateToMapBounds() {
        const {updateLocation, map: {search}} = this.props;
        const map = this.map.current.leafletElement;
        updateLocation(getMapBounds(map), search);
    }

    render() {
        const {map: {search, aspects, bounds, rooms: mapRooms}, toggleMapSearch} = this.props;
        const {aspectBounds, aspectsLoaded, loading} = this.state;

        return (
            <Dimmer.Dimmable>
                <Dimmer active={loading} inverted styleName="map-dimmer">
                    <Loader />
                </Dimmer>
                {aspectsLoaded && (
                    <RoomBookingMap mapRef={this.map} bounds={aspectBounds} onMove={this.onMove}
                                    searchCheckbox isSearchEnabled={search}
                                    onToggleSearchCheckbox={(e, data) => toggleMapSearch(data.checked, bounds)}
                                    aspects={aspects}
                                    onChangeAspect={(e, data) => this.onChangeAspect(data.value)}
                                    rooms={mapRooms}
                                    onLoad={this.onMapLoad} />
                )}
            </Dimmer.Dimmable>
        );
    }
}
