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
import {Dimmer, Grid} from 'semantic-ui-react';
import {connect} from 'react-redux';

import {Translate} from 'indico/react/i18n';
import {Preloader} from 'indico/react/util';
import TimelineBase from '../../components/TimelineBase';
import * as calendarActions from './actions';
import * as calendarSelectors from './selectors';
import * as roomActions from '../../common/rooms/actions';
import * as roomSelectors from '../../common/rooms/selectors';

import EditableTimelineItem from '../../components/EditableTimelineItem';
import BookFromListModal from '../../components/modals/BookFromListModal';


import '../../components/Timeline.module.scss';


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
        }).isRequired
    };

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

    render() {
        const {isFetching, calendarData: {date, rows}, actions: {setDate, fetchRoomDetails}} = this.props;
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
                    <TimelineBase minHour={6}
                                  maxHour={22}
                                  legendLabels={legendLabels}
                                  rows={rows.map(this._getRowSerializer(date || moment().format('YYYY-MM-DD')))}
                                  activeDate={date ? moment(date) : moment()}
                                  onDateChange={setDate}
                                  isLoading={isFetching}
                                  itemClass={EditableTimelineItem}
                                  itemProps={{onAddSlot: this.onAddSlot}}
                                  longLabel />
                </Grid.Row>
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
        rooms: roomSelectors.getAllRooms(state)
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchCalendar: calendarActions.fetchCalendar,
            fetchRoomDetails: roomActions.fetchDetails,
            setDate: (date) => calendarActions.setDate(date.format('YYYY-MM-DD')),
        }, dispatch)
    })
)(Calendar);
