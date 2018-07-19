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
import {Button, Card, Grid, Dimmer, Loader, Popup, Sticky} from 'semantic-ui-react';
import {Route} from 'react-router-dom';
import LazyScroll from 'redux-lazy-scroll';

import {Preloader, Slot} from 'indico/react/util';
import {Param, Plural, PluralTranslate, Translate, Singular} from 'indico/react/i18n';
import RoomFilterBar from '../RoomFilterBar';
import filterBarFactory from '../../containers/FilterBar';
import searchBarFactory from '../../containers/SearchBar';
import mapControllerFactory from '../../containers/MapController';
import Room from '../../containers/Room';
import roomDetailsModalFactory from '../modals/RoomDetailsModal';
import BookFromListModal from '../modals/BookFromListModal';

import './RoomList.module.scss';


const FilterBar = filterBarFactory('roomList', RoomFilterBar);
const SearchBar = searchBarFactory('roomList');
const MapController = mapControllerFactory('roomList');
const RoomDetailsModal = roomDetailsModalFactory('roomList');


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
        }).isRequired,
        pushState: PropTypes.func.isRequired,
    };

    constructor(props) {
        super(props);
        this.contextRef = React.createRef();
    }

    renderRoom = (room) => {
        const {id} = room;
        const {pushState} = this.props;
        const showDetailsBtn = (
            <Button primary icon="search" circular onClick={() => {
                pushState(`/rooms/${id}/details`);
            }} />
        );

        return (
            <Room key={room.id} room={room} showFavoriteButton>
                <Slot name="actions">
                    <Popup trigger={showDetailsBtn} content={Translate.string('Room details')} position="top center" />
                </Slot>
            </Room>
        );
    };

    closeBookingModal = () => {
        const {pushState} = this.props;
        pushState('/rooms', true);
    };

    roomPreloader(componentFunc) {
        const {fetchRoomDetails} = this.props;
        return ({match: {params: {roomId}}}) => (
            <Preloader checkCached={({roomDetails: {rooms: cachedRooms}}) => !!cachedRooms[roomId]}
                       action={() => fetchRoomDetails(roomId)}
                       dimmer={<Dimmer page />}>
                {() => componentFunc(roomId)}
            </Preloader>
        );
    }

    render() {
        const {rooms: {list, total, isFetching}, fetchRooms, roomDetails} = this.props;
        return (
            <Grid columns={2}>
                <Grid.Column width={11}>
                    <div className="ui" styleName="room-list" ref={this.contextRef}>
                        <Sticky context={this.contextRef.current} className="sticky-filters">
                            <Grid>
                                <Grid.Column width={16}>
                                    <FilterBar />
                                </Grid.Column>
                            </Grid>
                            <SearchBar onConfirm={fetchRooms} onTextChange={fetchRooms} />
                        </Sticky>
                        <div styleName="results-count">
                            {total === 0 && !isFetching && Translate.string('There are no rooms matching the criteria')}
                            {total !== 0 && (
                                <PluralTranslate count={total}>
                                    <Singular>
                                        There is <Param name="count" value={total} /> room matching the criteria
                                    </Singular>
                                    <Plural>
                                        There are <Param name="count" value={total} /> rooms matching the criteria
                                    </Plural>
                                </PluralTranslate>
                            )}
                        </div>
                        <LazyScroll hasMore={total > list.length} loadMore={() => fetchRooms(false)}
                                    isFetching={isFetching}>
                            <Card.Group stackable>
                                {list.map(this.renderRoom)}
                            </Card.Group>
                            <Loader active={isFetching} inline="centered" styleName="rooms-loader" />
                        </LazyScroll>
                    </div>
                    <Dimmer.Dimmable>
                        <Dimmer active={roomDetails.isFetching} page>
                            <Loader />
                        </Dimmer>
                    </Dimmer.Dimmable>
                </Grid.Column>
                <Grid.Column width={5}>
                    <MapController />
                </Grid.Column>
                <Route exact path="/rooms/:roomId/details" render={this.roomPreloader((roomId) => (
                    <RoomDetailsModal roomDetails={roomDetails.rooms[roomId]}
                                      onClose={this.closeBookingModal} />
                ))} />
                <Route exact path="/rooms/:roomId/book" render={this.roomPreloader((roomId) => (
                    <BookFromListModal room={roomDetails.rooms[roomId]}
                                       onClose={this.closeBookingModal} />
                ))} />
            </Grid>
        );
    }
}
