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
import {bindActionCreators} from 'redux';
import {Route} from 'react-router-dom';
import {Container, Dimmer, Grid, Loader, Sticky} from 'semantic-ui-react';
import {connect} from 'react-redux';

import {Translate} from 'indico/react/i18n';
import {Preloader} from 'indico/react/util';
import {serializeDate} from 'indico/utils/date';
import TimelineBase from '../../components/TimelineBase';
import roomDetailsModalFactory from '../../components/modals/RoomDetailsModal';
import {pushStateMergeProps, roomPreloader} from '../../util';
import * as calendarActions from './actions';
import * as calendarSelectors from './selectors';
import * as roomActions from '../../common/rooms/actions';
import * as roomSelectors from '../../common/rooms/selectors';
import {selectors as roomsSelectors} from '../../common/rooms';
import EditableTimelineItem from '../../components/EditableTimelineItem';
import BookFromListModal from '../../components/modals/BookFromListModal';
import TimelineHeader from '../../components/TimelineHeader';

import '../../components/Timeline.module.scss';


const RoomDetailsModal = roomDetailsModalFactory('calendar');

class Calendar extends React.Component {
    static propTypes = {
        calendarData: PropTypes.shape({
            date: PropTypes.string,
            rows: PropTypes.arrayOf(PropTypes.object).isRequired,
        }).isRequired,
        isFetching: PropTypes.bool.isRequired,
        actions: PropTypes.exact({
            fetchCalendar: PropTypes.func.isRequired,
            setDate: PropTypes.func.isRequired,
            fetchRoomDetails: PropTypes.func.isRequired
        }).isRequired,
        pushState: PropTypes.func.isRequired,
        roomDetailsFetching: PropTypes.bool.isRequired
    };


    constructor(props) {
        super(props);
        this.contextRef = React.createRef();
    }

    state = {};

    componentDidMount() {
        const {actions: {fetchCalendar}} = this.props;
        fetchCalendar();
    }

    componentDidUpdate({calendarData: {date: prevDate}}) {
        const {calendarData: {date}, actions: {fetchCalendar}} = this.props;
        if (prevDate !== date) {
            fetchCalendar();
        }
    }

    _getRowSerializer(day) {
        return ({bookings, pre_bookings: preBookings, nonbookable_periods: nonbookablePeriods,
                 unbookable_hours: unbookableHours, blockings, room}) => ({
            availability: {
                preBookings: preBookings[day] || [],
                bookings: bookings[day] || [],
                nonbookablePeriods: nonbookablePeriods[day] || [],
                unbookableHours: unbookableHours || [],
                blockings: blockings[day] || []
            },
            label: room.full_name,
            key: room.id,
            room
        });
    }

    onAddSlot = ({room: {id}, slotStartTime, slotEndTime}) => {
        const {calendarData: {date}} = this.props;
        this.setState({
            bookingRoomId: id,
            modalFields: {
                dates: {
                    startDate: moment(date, 'YYYY-MM-DD'),
                    endDate: null
                },
                timeSlot: {
                    startTime: moment(slotStartTime, 'hh:mm'),
                    endTime: moment(slotEndTime, 'hh:mm')
                },
                recurrence: {type: 'single'}
            }
        });
    };

    onCloseBookingModal = () => {
        this.setState({
            bookingRoomId: null,
            modalFields: null
        });
    };

    onClickLabel = (id) => {
        const {pushState} = this.props;
        pushState(`/calendar/${id}/details`);
    };

    closeModal = () => {
        const {pushState} = this.props;
        pushState('/calendar');
    };

    render() {
        const {
            isFetching, calendarData: {date, rows}, actions: {setDate, fetchRoomDetails}, roomDetailsFetching
        } = this.props;
        const {bookingRoomId, modalFields} = this.state;
        const legendLabels = [
            {label: Translate.string('Booked'), color: 'orange'},
            {label: Translate.string('Pre-Booking'), style: 'pre-booking'},
            {label: Translate.string('Blocked'), style: 'blocking'},
            {label: Translate.string('Not bookable'), style: 'unbookable'}
        ];

        return (
            <Grid>
                <Grid.Row>
                    <Container>
                        <div ref={this.contextRef}>
                            <Sticky context={this.contextRef.current} className="sticky-filters">
                                <TimelineHeader activeDate={date ? moment(date) : moment()}
                                                onDateChange={setDate}
                                                legendLabels={legendLabels} />
                            </Sticky>
                            <TimelineBase minHour={6}
                                          maxHour={22}
                                          rows={rows.map(this._getRowSerializer(date || serializeDate(moment())))}
                                          isLoading={isFetching}
                                          itemClass={EditableTimelineItem}
                                          itemProps={{onAddSlot: this.onAddSlot}}
                                          longLabel />
                            <Dimmer.Dimmable>
                                <Dimmer active={roomDetailsFetching} page>
                                    <Loader />
                                </Dimmer>
                            </Dimmer.Dimmable>
                        </div>
                    </Container>
                </Grid.Row>
                <Route exact path="/calendar/:roomId/details" render={roomPreloader((roomId) => (
                    <RoomDetailsModal roomId={roomId} onClose={this.closeModal} />
                ), fetchRoomDetails)} />
                <Route exact path="/calendar/:roomId/book" render={roomPreloader((roomId) => (
                    <BookFromListModal roomId={roomId} onClose={this.closeModal} />
                ), fetchRoomDetails)} />
                {bookingRoomId && (
                    <Preloader checkCached={state => !!roomSelectors.hasDetails(state, {roomId: bookingRoomId})}
                               action={() => fetchRoomDetails(bookingRoomId)}
                               dimmer={<Dimmer page />}>
                        {() => (
                            <BookFromListModal roomId={bookingRoomId}
                                               onClose={this.onCloseBookingModal}
                                               defaults={modalFields} />
                        )}
                    </Preloader>
                )}
            </Grid>
        );
    }
}


export default connect(
    state => ({
        isFetching: calendarSelectors.isFetching(state),
        calendarData: calendarSelectors.getCalendarData(state),
        rooms: roomSelectors.getAllRooms(state),
        roomDetailsFetching: roomsSelectors.isFetchingDetails(state)
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchCalendar: calendarActions.fetchCalendar,
            fetchRoomDetails: roomActions.fetchDetails,
            setDate: (date) => calendarActions.setDate(date.format(date)),
        }, dispatch),
        dispatch
    }),
    pushStateMergeProps
)(Calendar);
