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

import propTypes from 'prop-types';
import React from 'react';
import {Grid} from 'semantic-ui-react';

import filterBarFactory from '../../containers/FilterBar';
import RoomBookingMap from '../RoomBookingMap';


export default class BookRoom extends React.Component {
    static propTypes = {
        fetchMapDefaultLocation: propTypes.func.isRequired,
        updateLocation: propTypes.func.isRequired,
        bounds: propTypes.array,
        search: propTypes.bool.isRequired,
        toggleMapSearch: propTypes.func.isRequired,
    };

    static defaultProps = {
        bounds: null
    };

    constructor(props) {
        super(props);
        const {fetchMapDefaultLocation, bounds} = props;
        if (!bounds) {
            fetchMapDefaultLocation();
        }
    }

    onMove(e) {
        const {updateLocation} = this.props;
        const boundsObj = e.target.getBounds();
        const location = [
            Object.values(boundsObj.getNorthWest()),
            Object.values(boundsObj.getSouthEast())
        ];
        updateLocation(location);
    }

    render() {
        const {bounds, toggleMapSearch, search} = this.props;
        const FilterBar = filterBarFactory('bookRoom');
        return (
            <Grid columns={2}>
                <Grid.Column width={11}>
                    <FilterBar />
                </Grid.Column>
                <Grid.Column width={5}>
                    {bounds && (
                        <RoomBookingMap bounds={bounds} onMove={(e) => this.onMove(e)}
                                        searchCheckbox isSearchEnabled={search}
                                        onToggleSearchCheckbox={(e, data) => toggleMapSearch(data.checked)} />
                    )}
                </Grid.Column>
            </Grid>
        );
    }
}
