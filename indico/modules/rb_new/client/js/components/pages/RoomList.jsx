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
import {Button, Grid, Dimmer, Loader, Popup} from 'semantic-ui-react';

import {Slot} from 'indico/react/util';
import {Translate} from 'indico/react/i18n';
import RoomSearchPane from '../RoomSearchPane';
import RoomFilterBar from '../RoomFilterBar';
import filterBarFactory from '../../containers/FilterBar';
import searchBarFactory from '../../containers/SearchBar';
import mapControllerFactory from '../../containers/MapController';
import Room from '../../containers/Room';
import RoomDetailsModal from '../modals/RoomDetailsModal';


const FilterBar = filterBarFactory('roomList', RoomFilterBar);
const SearchBar = searchBarFactory('roomList');
const MapController = mapControllerFactory('roomList');


export default class RoomList extends React.Component {
    static propTypes = {
        fetchRooms: PropTypes.func.isRequired,
        rooms: PropTypes.shape({
            list: PropTypes.array,
            isFetching: PropTypes.bool,
        }).isRequired,
        fetchRoomDetails: PropTypes.func.isRequired,
        roomDetails: PropTypes.shape({
            list: PropTypes.array,
            isFetching: PropTypes.bool,
            currentViewID: PropTypes.number,
        }).isRequired,
        setRoomDetailsModal: PropTypes.func.isRequired,
    };

    handleOpenModal = (id) => {
        const {fetchRoomDetails, setRoomDetailsModal} = this.props;
        fetchRoomDetails(id);
        setRoomDetailsModal(id);
    };

    renderRoom = (room) => {
        const showDetailsBtn = <Button primary icon="search" circular onClick={() => this.handleOpenModal(room.id)} />;
        return (
            <Room key={room.id} room={room} showFavoriteButton>
                <Slot name="actions">
                    <Popup trigger={showDetailsBtn} content={Translate.string('Room details')} position="top center" />
                </Slot>
            </Room>
        );
    };

    render() {
        const {rooms, fetchRooms, roomDetails, setRoomDetailsModal} = this.props;
        return (
            <Grid columns={2}>
                <Grid.Column width={11}>
                    <RoomSearchPane rooms={rooms}
                                    fetchRooms={fetchRooms}
                                    filterBar={<FilterBar />}
                                    searchBar={<SearchBar onConfirm={fetchRooms} onTextChange={fetchRooms} />}
                                    renderRoom={this.renderRoom} />
                    <Dimmer.Dimmable>
                        <Dimmer active={roomDetails.isFetching} page>
                            <Loader />
                        </Dimmer>
                        <RoomDetailsModal roomDetails={roomDetails} setRoomDetailsModal={setRoomDetailsModal} />
                    </Dimmer.Dimmable>
                </Grid.Column>
                <Grid.Column width={5}>
                    <MapController />
                </Grid.Column>
            </Grid>
        );
    }
}
