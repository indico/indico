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

/* eslint "react/forbid-component-props": "off" */

import React from 'react';
import PropTypes from 'prop-types';
import {Grid} from 'semantic-ui-react';

import RoomBookingMap from '../RoomBookingMap';
import RoomSearchPane from '../RoomSearchPane';
import RoomFilterBar from '../RoomFilterBar';
import filterBarFactory from '../../containers/FilterBar';
import searchBarFactory from '../../containers/SearchBar';
import {getMapBounds} from '../../util';


const FilterBar = filterBarFactory('roomList', RoomFilterBar);
const SearchBar = searchBarFactory('roomList');


export default class RoomList extends React.Component {
    static propTypes = {
        fetchRooms: PropTypes.func.isRequired,
        fetchMapDefaultAspects: PropTypes.func.isRequired,
        map: PropTypes.shape({
            bounds: PropTypes.array,
        }).isRequired,
        updateLocation: PropTypes.func.isRequired,
    };

    constructor(props) {
        super(props);
        const {map: {bounds}, fetchMapDefaultAspects} = this.props;
        if (!bounds) {
            fetchMapDefaultAspects();
        }
    }

    componentDidMount() {
        const {fetchRooms} = this.props;
        fetchRooms();
    }

    onMove(e) {
        const {updateLocation} = this.props;
        updateLocation(getMapBounds(e.target));
    }

    render() {
        const {fetchRooms, map: {bounds}} = this.props;
        return (
            <Grid columns={2}>
                <Grid.Column width={11}>
                    <RoomSearchPane {...this.props}
                                    filterBar={<FilterBar />}
                                    searchBar={<SearchBar onConfirm={fetchRooms} onTextChange={fetchRooms} />} />
                </Grid.Column>
                <Grid.Column width={5}>
                    {bounds && (
                        <RoomBookingMap bounds={bounds} onMove={(e) => this.onMove(e)} />
                    )}
                </Grid.Column>
            </Grid>
        );
    }
}
