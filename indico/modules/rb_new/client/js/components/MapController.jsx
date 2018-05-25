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
import React from 'react';
import PropTypes from 'prop-types';
import {Button, Checkbox, Dimmer, Dropdown, Loader, Popup} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

import {getAspectBounds, getMapBounds, getRoomListBounds, checkRoomsInBounds} from '../util';
import RoomBookingMap, {RoomBookingMapControl} from './RoomBookingMap';

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

    static getDerivedStateFromProps({filterBounds, map: {bounds}}, prevState) {
        const aspectBounds = filterBounds || bounds;
        return {
            ...prevState,
            // Take the user-set bounds, otherwise default to the map's default bounds.
            aspectBounds
        };
    }

    constructor(props) {
        super(props);
        this.mapRef = React.createRef();

        this.state = {
            loading: true,
            aspectsLoaded: false,
            allRoomsVisible: false
        };
    }

    async componentDidMount() {
        const {fetchRooms} = this.props;
        fetchRooms();
        this.loadAspects();
    }

    componentDidUpdate() {
        // check whether rooms are in bounds in parallel, to
        // avoid blocking the main thread with the calculations
        _.defer(() => {
            const {map: {bounds, rooms}} = this.props;
            const {allRoomsVisible} = this.state;
            const inBounds = !bounds || checkRoomsInBounds(rooms, bounds);
            if (inBounds !== allRoomsVisible) {
                this.setState({
                    allRoomsVisible: !rooms.length || inBounds
                });
            }
        });
    }

    async loadAspects() {
        const {fetchMapDefaultAspects} = this.props;
        const {aspectsLoaded} = this.state;

        if (!aspectsLoaded) {
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
        this.setState({
            aspectBounds: getAspectBounds(aspects[aspectIdx])
        });
    }

    updateToMapBounds = () => {
        const {updateLocation, map: {search}} = this.props;
        if (this.mapRef.current) {
            const map = this.mapRef.current.leafletElement;
            updateLocation(getMapBounds(map), search);
        }
    };

    showAllRooms = () => {
        const {map: {rooms}} = this.props;
        this.setState({
            aspectBounds: getRoomListBounds(rooms),
            allRoomsVisible: true
        });
    };

    render() {
        const {map: {search, aspects, bounds, rooms}} = this.props;
        const {aspectBounds, aspectsLoaded, loading, allRoomsVisible} = this.state;
        const aspectOptions = Object.entries(aspects).map(([key, val]) => ({
            text: val.name,
            value: Number(key)
        }));

        const searchControl = (
            <RoomBookingMapControl position="topleft">
                <Checkbox label={Translate.string('Search as I move the map')}
                          onChange={(e, data) => this.toggleMapSearch(data.checked, bounds)}
                          checked={search} styleName="map-control-content" />
            </RoomBookingMapControl>
        );

        const aspectsControl = !!aspects.length && (
            <RoomBookingMapControl position="bottomleft">
                <Dropdown placeholder={Translate.string('Select aspect')} selection upward
                          options={aspectOptions} defaultValue={aspects.findIndex(op => op.default_on_startup)}
                          styleName="aspects-dropdown map-control-content"
                          openOnFocus={false} onChange={(e, data) => this.onChangeAspect(data.value)} />
            </RoomBookingMapControl>
        );

        const showAllButton = (
            <Button icon="expand"
                    styleName="show-all-button map-control-content"
                    onClick={this.showAllRooms}
                    disabled={allRoomsVisible} />
        );

        const showAllControl = (
            <RoomBookingMapControl position="bottomright">
                <Popup trigger={showAllButton}
                       content={Translate.string('Zoom out to include all listed rooms')} />
            </RoomBookingMapControl>
        );

        return (
            <Dimmer.Dimmable>
                <Dimmer active={loading} inverted styleName="map-dimmer">
                    <Loader />
                </Dimmer>
                {aspectsLoaded && (
                    <RoomBookingMap mapRef={this.mapRef}
                                    bounds={aspectBounds}
                                    aspects={aspects}
                                    rooms={rooms}
                                    onLoad={this.onMapLoad}
                                    onMove={this.onMove}>
                        {searchControl}
                        {aspectsControl}
                        {showAllControl}
                    </RoomBookingMap>
                )}
            </Dimmer.Dimmable>
        );
    }
}
