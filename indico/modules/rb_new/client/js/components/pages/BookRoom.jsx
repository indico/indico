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

import PropTypes from 'prop-types';
import React from 'react';
import {Grid, Icon, Message} from 'semantic-ui-react';

import {Slot} from 'indico/react/util';
import mapControllerFactory from '../../containers/MapController';
import RoomSearchPane from '../RoomSearchPane';
import BookingFilterBar from '../BookingFilterBar';
import filterBarFactory from '../../containers/FilterBar';
import searchBoxFactory from '../../containers/SearchBar';
import Room from '../Room';


const FilterBar = filterBarFactory('bookRoom', BookingFilterBar);
const SearchBar = searchBoxFactory('bookRoom');
const MapController = mapControllerFactory('bookRoom');


export default class BookRoom extends React.Component {
    static propTypes = {
        rooms: PropTypes.shape({
            list: PropTypes.array,
            isFetching: PropTypes.bool,
        }).isRequired,
        fetchRooms: PropTypes.func.isRequired
    };

    renderRoom = (room) => {
        return (
            <Room key={room.id} room={room}>
                <Slot>
                    <Grid centered columns={3} style={{margin: 0, height: '100%', opacity: 0.9}}>
                        <Grid.Column verticalAlign="middle" width={14}>
                            <Message size="mini" warning compact>
                                <Message.Header>
                                    <Icon name="clock" /> 25 minutes later
                                </Message.Header>
                            </Message>
                        </Grid.Column>
                    </Grid>
                </Slot>
            </Room>
        );
    };

    render() {
        const {rooms, fetchRooms} = this.props;
        return (
            <Grid columns={2}>
                <Grid.Column width={11}>
                    <RoomSearchPane rooms={rooms}
                                    fetchRooms={fetchRooms}
                                    filterBar={<FilterBar />}
                                    searchBar={<SearchBar onConfirm={fetchRooms} onTextChange={fetchRooms} />}
                                    renderRoom={this.renderRoom} />
                </Grid.Column>
                <Grid.Column width={5}>
                    <MapController />
                </Grid.Column>
            </Grid>
        );
    }
}
