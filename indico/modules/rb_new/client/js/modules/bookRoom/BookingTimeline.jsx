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
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {stateToQueryString} from 'redux-router-querystring';
import {Message, Segment} from 'semantic-ui-react';
import {Translate, Param} from 'indico/react/i18n';
import {serializeDate, toMoment} from 'indico/utils/date';
import TimelineBase from '../../components/TimelineBase';
import {isDateWithinRange, pushStateMergeProps} from '../../util';
import {queryString as queryStringSerializer} from '../../serializers/filters';
import * as selectors from './selectors';

import '../../components/Timeline.module.scss';


export class BookingTimelineComponent extends React.Component {
    static propTypes = {
        minHour: PropTypes.number.isRequired,
        maxHour: PropTypes.number.isRequired,
        availability: PropTypes.array.isRequired,
        dateRange: PropTypes.array.isRequired,
        pushState: PropTypes.func.isRequired,
        loadMore: PropTypes.func,

        // from redux state
        isFetching: PropTypes.bool.isRequired,
        isFetchingRooms: PropTypes.bool.isRequired,
        recurrenceType: PropTypes.string.isRequired,
        rooms: PropTypes.object
    };

    static defaultProps = {
        loadMore: null,
        rooms: null
    };

    state = {};

    static getDerivedStateFromProps({dateRange}, state) {
        if (!_.isEmpty(dateRange) && !isDateWithinRange(state.activeDate, dateRange, toMoment)) {
            return {...state, activeDate: toMoment(dateRange[0])};
        } else {
            return state;
        }
    }

    get singleRoom() {
        const {availability} = this.props;
        return availability.length === 1 && availability[0][1];
    }

    _getRowSerializer(dt, singleRoom = false) {
        return ({candidates, pre_bookings: preBookings, bookings, pre_conflicts: preConflicts, conflicts,
                 blockings, nonbookable_periods: nonbookablePeriods, unbookable_hours: unbookableHours,
                 room}) => {
            const hasConflicts = conflicts[dt] && conflicts[dt].length !== 0;
            const av = {
                candidates: candidates[dt].map((cand) => ({...cand, bookable: !hasConflicts})) || [],
                preBookings: preBookings[dt] || [],
                bookings: bookings[dt] || [],
                conflicts: conflicts[dt] || [],
                preConflicts: preConflicts[dt] || [],
                blockings: blockings[dt] || [],
                nonbookablePeriods: nonbookablePeriods[dt] || [],
                unbookableHours: unbookableHours || []
            };
            const {full_name: fullName, id} = room;

            return {
                availability: av,
                label: singleRoom ? moment(dt).format('L') : fullName,
                key: singleRoom ? dt : id,
                conflictIndicator: true,
                room
            };
        };
    }

    calcRows = () => {
        const {activeDate} = this.state;
        const {availability, dateRange} = this.props;

        if (this.singleRoom) {
            const roomAvailability = this.singleRoom;
            return dateRange.map(dt => this._getRowSerializer(dt, true)(roomAvailability));
        } else {
            const dt = serializeDate(activeDate);
            return availability.map(([, data]) => data).map(this._getRowSerializer(dt));
        }
    };

    openBookingModal = (room) => {
        const {pushState} = this.props;
        pushState(`/book/${room.id}/confirm`, true);
    };

    renderRoomSummary({room: {full_name: fullName}}) {
        return (
            <Segment>
                <Translate>Availability for room <Param name="roomName" value={<strong>{fullName}</strong>} /></Translate>
            </Segment>
        );
    }

    render() {
        const {
            dateRange, isFetching, maxHour, minHour, isFetchingRooms, recurrenceType, rooms, loadMore
        } = this.props;
        const {activeDate} = this.state;
        const legendLabels = [
            {label: Translate.string('Available'), color: 'green'},
            {label: Translate.string('Booked'), color: 'orange'},
            {label: Translate.string('Pre-Booking'), style: 'pre-booking'},
            {label: Translate.string('Conflict'), color: 'red'},
            {label: Translate.string('Conflict with Pre-Booking'), style: 'pre-booking-conflict'},
            {label: Translate.string('Blocked'), style: 'blocking'},
            {label: Translate.string('Not bookable'), style: 'unbookable'}
        ];
        const emptyMessage = (
            <Message warning>
                <Translate>
                    There are no rooms matching the criteria.
                </Translate>
            </Message>
        );

        if (!activeDate) {
            // this happens for a short time when loading the timeline with a direct link
            return null;
        }

        const props = {};
        if (loadMore && rooms) {
            props.lazyScroll = {
                loadMore,
                hasMore: rooms.matching > rooms.list.length,
                isFetching: isFetching || isFetchingRooms
            };
        }

        return (
            <TimelineBase {...props}
                          rows={this.calcRows()}
                          legendLabels={legendLabels}
                          emptyMessage={emptyMessage}
                          onClick={this.openBookingModal}
                          dateRange={dateRange}
                          minHour={minHour}
                          maxHour={maxHour}
                          activeDate={activeDate}
                          onDateChange={(newDate) => {
                              this.setState({
                                  activeDate: newDate
                              });
                          }}
                          extraContent={this.singleRoom && this.renderRoomSummary(this.singleRoom)}
                          isLoading={isFetching || isFetchingRooms}
                          recurrenceType={recurrenceType}
                          disableDatePicker={!!this.singleRoom} />
        );
    }
}

export default connect(
    state => {
        const {bookRoom} = state;
        return {
            ...bookRoom.timeline,
            rooms: bookRoom.rooms,
            recurrenceType: bookRoom.filters.recurrence.type,
            queryString: stateToQueryString(bookRoom, queryStringSerializer),
            isFetchingRooms: selectors.isFetchingRooms(state)
        };
    },
    dispatch => ({
        dispatch
    }),
    pushStateMergeProps
)(BookingTimelineComponent);
