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
import _ from 'lodash';
import {Button, Dimmer, Grid, Icon, Loader, Message, Sticky} from 'semantic-ui-react';

import {Slot, toClasses} from 'indico/react/util';
import mapControllerFactory from '../../containers/MapController';
import RoomSearchPane from '../RoomSearchPane';
import BookingFilterBar from '../BookingFilterBar';
import filterBarFactory from '../../containers/FilterBar';
import searchBoxFactory from '../../containers/SearchBar';
import Room from '../Room';
import Timeline from '../../containers/Timeline';
import BookRoomModal from '../../containers/BookRoomModal';
import RoomDetailsModal from '../modals/RoomDetailsModal';

import './BookRoom.module.scss';


const FilterBar = filterBarFactory('bookRoom', BookingFilterBar);
const SearchBar = searchBoxFactory('bookRoom');
const MapController = mapControllerFactory('bookRoom');


export default class BookRoom extends React.Component {
    static propTypes = {
        setFilterParameter: PropTypes.func.isRequired,
        rooms: PropTypes.shape({
            list: PropTypes.array,
            isFetching: PropTypes.bool,
        }).isRequired,
        fetchRooms: PropTypes.func.isRequired,
        timeline: PropTypes.object.isRequired,
        clearRoomList: PropTypes.func.isRequired,
        roomDetails: PropTypes.shape({
            list: PropTypes.array,
            isFetching: PropTypes.bool,
            currentViewID: PropTypes.number,
        }).isRequired,
        fetchRoomDetails: PropTypes.func.isRequired,
        setRoomDetailsModal: PropTypes.func.isRequired,
        resetBookingState: PropTypes.func.isRequired
    };

    constructor(props) {
        super(props);
        this.state = {
            view: 'book'
        };
    }

    componentWillUnmount() {
        const {setFilterParameter, clearRoomList} = this.props;
        setFilterParameter('text', null);
        clearRoomList();
    }

    openDetailsModal = (id) => {
        const {fetchRoomDetails, setRoomDetailsModal} = this.props;
        fetchRoomDetails(id);
        setRoomDetailsModal(id);
    };

    openBookingModal = (room) => {
        this.setState({
            bookingModal: true,
            selectedRoom: room
        });
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
                <Slot name="actions">
                    <Button positive icon="check" circular onClick={() => this.openBookingModal(room)} />
                    <Button primary icon="search" circular onClick={() => this.openDetailsModal(room.id)} />
                </Slot>
            </Room>
        );
    };

    renderMainContent = () => {
        const {view, timelineRef} = this.state;
        const {fetchRooms, roomDetails, rooms, setRoomDetailsModal} = this.props;
        const filterBar = <FilterBar />;
        const searchBar = <SearchBar onConfirm={fetchRooms} onTextChange={fetchRooms} />;

        if (view === 'book') {
            return (
                <>
                    <RoomSearchPane rooms={rooms}
                                    fetchRooms={fetchRooms}
                                    filterBar={filterBar}
                                    searchBar={searchBar}
                                    renderRoom={this.renderRoom}
                                    extraIcons={this.renderViewSwitch()} />
                    <Dimmer.Dimmable>
                        <Dimmer active={roomDetails.isFetching} page>
                            <Loader />
                        </Dimmer>
                        <RoomDetailsModal roomDetails={roomDetails}
                                          setRoomDetailsModal={setRoomDetailsModal} />
                    </Dimmer.Dimmable>
                </>
            );
        } else if (view === 'timeline') {
            return (
                <div ref={(ref) => this.handleContextRef(ref, 'timelineRef')}>
                    <Sticky context={timelineRef} className="sticky-filters">
                        <Grid>
                            <Grid.Column width={13}>
                                {filterBar}
                            </Grid.Column>
                            {this.renderViewSwitch()}
                        </Grid>
                        <Grid.Row>
                            {searchBar}
                        </Grid.Row>
                    </Sticky>
                    <Timeline minHour={6} maxHour={22} />
                </div>
            );
        }
    };

    renderViewSwitch() {
        const {switcherRef, view} = this.state;
        const {timeline: {availability}} = this.props;
        const timelineDataAvailable = !_.isEmpty(availability);
        const hasConflicts = Object.values(availability).some((data) => {
            return !_.isEmpty(data.conflicts);
        });
        const classes = toClasses({active: view === 'timeline', disabled: !timelineDataAvailable});

        return (
            <Grid.Column width={3} styleName="view-icons" textAlign="right" verticalAlign="middle">
                <div ref={(ref) => this.handleContextRef(ref, 'switcherRef')} styleName="view-icons-context">
                    <Sticky context={switcherRef} offset={30}>
                        <span>
                            <Icon size="big" className={toClasses({active: view === 'book'})}
                                  name="list" onClick={() => this.setState({view: 'book', timelineRef: null})} />
                            <Icon.Group size="big"
                                        className={classes}
                                        onClick={this.switchToTimeline}>
                                <Icon name="calendar outline" disabled={!timelineDataAvailable} />
                                {hasConflicts && (
                                    <Icon name="exclamation triangle" color="red" corner />
                                )}
                            </Icon.Group>
                        </span>
                    </Sticky>
                </div>
            </Grid.Column>
        );
    }

    switchToTimeline = () => {
        const {timeline: {availability}} = this.props;
        const timelineDataAvailable = !_.isEmpty(availability);

        if (timelineDataAvailable) {
            this.setState({view: 'timeline'});
        }
    };

    handleContextRef = (ref, kind) => {
        if (kind in this.state) {
            const {[kind]: context} = this.state;
            if (context !== null) {
                return;
            }
        }
        this.setState({[kind]: ref});
    };

    closeBookingModal = () => {
        const {resetBookingState} = this.props;
        resetBookingState();
        this.setState({
            bookingModal: false
        });
    };

    render() {
        const {bookingModal, selectedRoom} = this.state;
        return (
            <Grid columns={2}>
                <Grid.Column width={11}>
                    {this.renderMainContent()}
                </Grid.Column>
                <Grid.Column width={5}>
                    <MapController />
                </Grid.Column>
                <BookRoomModal open={bookingModal}
                               room={selectedRoom}
                               onClose={this.closeBookingModal} />
            </Grid>
        );
    }
}
