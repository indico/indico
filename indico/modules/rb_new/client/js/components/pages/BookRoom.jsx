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


import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import _ from 'lodash';
import {Button, Card, Dimmer, Grid, Header, Icon, Label, Loader, Message, Popup, Sticky} from 'semantic-ui-react';
import {Slot, toClasses} from 'indico/react/util';
import {PluralTranslate, Translate, Singular, Param, Plural} from 'indico/react/i18n';
import mapControllerFactory from '../../containers/MapController';
import RoomSearchPane from '../RoomSearchPane';
import BookingFilterBar from '../BookingFilterBar';
import filterBarFactory from '../../containers/FilterBar';
import searchBoxFactory from '../../containers/SearchBar';
import Room from '../../containers/Room';
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
        clearTextFilter: PropTypes.func.isRequired,
        rooms: PropTypes.shape({
            list: PropTypes.array,
            isFetching: PropTypes.bool,
        }).isRequired,
        fetchRooms: PropTypes.func.isRequired,
        filters: PropTypes.object.isRequired,
        timeline: PropTypes.object.isRequired,
        clearRoomList: PropTypes.func.isRequired,
        roomDetails: PropTypes.shape({
            list: PropTypes.array,
            isFetching: PropTypes.bool,
            currentViewID: PropTypes.number,
        }).isRequired,
        fetchRoomDetails: PropTypes.func.isRequired,
        setRoomDetailsModal: PropTypes.func.isRequired,
        resetBookingState: PropTypes.func.isRequired,
        suggestions: PropTypes.object.isRequired
    };

    constructor(props) {
        super(props);
        this.state = {
            view: 'book'
        };
    }

    componentWillUnmount() {
        const {clearTextFilter, clearRoomList} = this.props;
        clearTextFilter();
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
        const bookingModalBtn = <Button positive icon="check" circular onClick={() => this.openBookingModal(room)} />;
        const showDetailsBtn = <Button primary icon="search" circular onClick={() => this.openDetailsModal(room.id)} />;
        return (
            <Room key={room.id} room={room} showFavoriteButton>
                <Slot name="actions">
                    <Popup trigger={bookingModalBtn} content={Translate.string('Book room')} position="top center" hideOnScroll />
                    <Popup trigger={showDetailsBtn} content={Translate.string('Room details')} position="top center" hideOnScroll />
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
                                    renderSuggestions={this.renderSuggestions}
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

    renderSuggestions = () => {
        const {suggestions} = this.props;

        if (!suggestions.list || !suggestions.list.length) {
            return;
        }

        return (
            <>
                <Header as="h2">
                    <Translate>Room suggestions</Translate>
                </Header>
                <Card.Group styleName="suggestions" stackable>
                    {suggestions.list.map((suggestion) => this.renderSuggestion(suggestion))}
                </Card.Group>
            </>
        );
    };

    renderSuggestion = ({room, suggestions}) => {
        return (
            <Room key={room.id} room={room}>
                <Slot>
                    <Grid centered styleName="suggestion" columns={3}>
                        <Grid.Column verticalAlign="middle" width={14}>
                            {this.renderSuggestionText(room, suggestions)}
                        </Grid.Column>
                    </Grid>
                </Slot>
            </Room>
        );
    };

    suggestionTooltip = (element) => (
        <Popup trigger={element} content={Translate.string('The filtering criteria will be adjusted accordingly')} />
    );

    renderSuggestionText = (room, {time, duration, skip}) => {
        return (
            <>
                {time && this.suggestionTooltip(
                    <Message styleName="suggestion-text" size="mini" onClick={() => this.updateFilters('time', time)}
                             warning compact>
                        <Message.Header>
                            <Icon name="clock" />
                            <PluralTranslate count={time}>
                                <Singular>
                                    One minute <Param name="modifier" value={time < 0 ? 'earlier' : 'later'} />
                                </Singular>
                                <Plural>
                                    <Param name="count" value={Math.abs(time)} /> minutes{' '}
                                    <Param name="modifier" value={time < 0 ? 'earlier' : 'later'} />
                                </Plural>
                            </PluralTranslate>
                        </Message.Header>
                    </Message>
                )}
                {duration && time && (
                    <div>
                        <Label color="brown" circular>{Translate.string('or')}</Label>
                    </div>
                )}
                {duration && this.suggestionTooltip(
                    <Message styleName="suggestion-text" size="mini" onClick={() => this.updateFilters('duration', duration)}
                             warning compact>
                        <Message.Header>
                            <Icon name="hourglass full" /> {PluralTranslate.string('One minute shorter', '{duration} minutes shorter', duration, {duration})}
                        </Message.Header>
                    </Message>
                )}
                {skip && (
                    <Message styleName="suggestion-text" size="mini" onClick={() => this.openBookingModal(room)}
                             warning compact>
                        <Message.Header>
                            <Icon name="calendar times" /> {PluralTranslate.string('Skip one day', 'Skip {skip} days', skip, {skip})}
                        </Message.Header>
                    </Message>
                )}
            </>
        );
    };

    updateFilters = (filter, value) => {
        const {setFilterParameter} = this.props;
        let {filters: {timeSlot: {startTime, endTime}}} = this.props;

        if (filter === 'duration') {
            endTime = moment(endTime, 'HH:mm').subtract(value, 'minutes').format('HH:mm');
        } else if (filter === 'time') {
            startTime = moment(startTime, 'HH:mm').add(value, 'minutes').format('HH:mm');
            endTime = moment(endTime, 'HH:mm').add(value, 'minutes').format('HH:mm');
        }
        setFilterParameter('timeSlot', {startTime, endTime});
    };

    renderViewSwitch() {
        const {switcherRef, view} = this.state;
        const {timeline: {availability}} = this.props;
        const timelineDataAvailable = !_.isEmpty(availability);
        const hasConflicts = Object.values(availability).some((data) => {
            return !_.isEmpty(data.conflicts);
        });
        const classes = toClasses({active: view === 'timeline', disabled: !timelineDataAvailable});

        const listIcon = (
            <Icon size="big" className={toClasses({active: view === 'book'})} name="grid layout"
                  onClick={() => this.setState({view: 'book', timelineRef: null})} />
        );
        const timelineIcon = <Icon name="calendar outline" disabled={!timelineDataAvailable} />;
        return (
            <Grid.Column width={3} styleName="view-icons" textAlign="right" verticalAlign="middle">
                <div ref={(ref) => this.handleContextRef(ref, 'switcherRef')} styleName="view-icons-context">
                    <Sticky context={switcherRef} offset={30}>
                        <span>
                            {view === 'timeline'
                                ? <Popup trigger={listIcon} content={Translate.string('List view')} />
                                : listIcon
                            }
                            <Icon.Group size="big"
                                        className={classes}
                                        onClick={this.switchToTimeline}>
                                {view === 'book'
                                    ? <Popup trigger={timelineIcon} content={Translate.string('Timeline view')} />
                                    : timelineIcon
                                }
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
