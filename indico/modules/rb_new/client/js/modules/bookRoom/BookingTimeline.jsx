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
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {stateToQueryString} from 'redux-router-querystring';
import {Message, Segment} from 'semantic-ui-react';
import {Translate, Param} from 'indico/react/i18n';
import {serializeDate, toMoment} from 'indico/utils/date';
import TimelineBase from '../../components/TimelineBase';
import {isDateWithinRange, pushStateMergeProps} from '../../util';
import {queryString as queryStringSerializer} from '../../serializers/filters';
import * as bookRoomActions from './actions';

import '../../components/Timeline.module.scss';
import * as bookRoomSelectors from './selectors';


const timelinePropTypes = {
    minHour: PropTypes.number.isRequired,
    maxHour: PropTypes.number.isRequired,
    availability: PropTypes.array.isRequired,
    dateRange: PropTypes.arrayOf(PropTypes.string).isRequired,
    recurrenceType: PropTypes.string.isRequired,
};

export class BookingTimelineComponent extends React.Component {
    static propTypes = {
        ...timelinePropTypes,
        pushState: PropTypes.func.isRequired,
        lazyScroll: PropTypes.object,
        isFetching: PropTypes.bool.isRequired,
        showEmptyMessage: PropTypes.bool,
        allowSingleRoom: PropTypes.bool,
    };

    static defaultProps = {
        lazyScroll: null,
        allowSingleRoom: true,
        showEmptyMessage: true,
    };

    state = {};

    static getDerivedStateFromProps({dateRange, defaultDate}, state) {
        if (!_.isEmpty(dateRange) && !isDateWithinRange(state.activeDate, dateRange, toMoment)) {
            return {...state, activeDate: toMoment(dateRange[0])};
        } else if (_.isEmpty(dateRange)) {
            return {...state, activeDate: toMoment(defaultDate)};
        } else {
            return state;
        }
    }

    get singleRoom() {
        const {availability, allowSingleRoom} = this.props;
        if (!allowSingleRoom || availability.length !== 1) {
            return null;
        }
        return availability[0][1];
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
            dateRange, isFetching, maxHour, minHour, recurrenceType, lazyScroll, showEmptyMessage
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
        const emptyMessage = showEmptyMessage ? (
            <Message warning>
                <Translate>
                    There are no rooms matching the criteria.
                </Translate>
            </Message>
        ) : null;

        if (!activeDate) {
            // this happens for a short time when loading the timeline with a direct link
            return null;
        }

        return (
            <TimelineBase lazyScroll={lazyScroll}
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
                          isLoading={isFetching}
                          recurrenceType={recurrenceType}
                          disableDatePicker={!!this.singleRoom} />
        );
    }
}

class BookingTimeline extends React.Component {
    static propTypes = {
        ...timelinePropTypes,
        fetchingTimeline: PropTypes.bool.isRequired,
        hasMoreTimelineData: PropTypes.bool.isRequired,
        filters: PropTypes.shape({
            dates: PropTypes.object.isRequired,
            timeSlot: PropTypes.object.isRequired,
            recurrence: PropTypes.object.isRequired,
        }).isRequired,
        pushState: PropTypes.func.isRequired,
        actions: PropTypes.exact({
            fetchTimeline: PropTypes.func.isRequired,
            initTimeline: PropTypes.func.isRequired,
            addTimelineRooms: PropTypes.func.isRequired,
            fetchRoomSuggestions: PropTypes.func.isRequired,
        }).isRequired,
    };

    componentDidMount() {
        const {
            actions: {initTimeline, fetchTimeline, fetchRoomSuggestions},
            filters: {dates, timeSlot, recurrence},
            roomIds,
            suggestedRoomIds,
        } = this.props;
        initTimeline(roomIds, dates, timeSlot, recurrence);
        if (roomIds.length) {
            fetchTimeline();
        }
        if (suggestedRoomIds.length) {
            this.processSuggestedRooms();
        } else {
            fetchRoomSuggestions();
        }
    }

    componentDidUpdate({roomIds: prevRoomIds, suggestedRoomIds: prevSuggestedRoomIds, filters: prevFilters}) {
        const {
            actions: {initTimeline, fetchTimeline, fetchRoomSuggestions},
            filters,
            roomIds,
            suggestedRoomIds,
        } = this.props;
        const {dates, timeSlot, recurrence} = filters;
        // reset the timeline when filters changed
        if (!_.isEqual(prevFilters, filters)) {
            initTimeline([], dates, timeSlot, recurrence);
        }
        // reset and update the timeline when the search results changed
        if (!_.isEqual(prevRoomIds, roomIds)) {
            initTimeline(roomIds, dates, timeSlot, recurrence);
            if (roomIds.length) {
                fetchTimeline();
            }
            if (!suggestedRoomIds.length) {
                fetchRoomSuggestions();
            }
        }
        if (!_.isEqual(prevSuggestedRoomIds, suggestedRoomIds) && suggestedRoomIds.length) {
            this.processSuggestedRooms();
        }
    }

    processSuggestedRooms() {
        const {
            actions: {fetchTimeline, addTimelineRooms},
            roomIds,
            suggestedRoomIds,
        } = this.props;
        addTimelineRooms(suggestedRoomIds);
        // if we have no normal results there is no lazy scroller to trigger the fetching
        if (!roomIds.length) {
            fetchTimeline();
        }
    }

    render() {
        const {
            fetchingTimeline,
            hasMoreTimelineData,
            pushState,
            minHour,
            maxHour,
            availability,
            dateRange,
            recurrenceType,
            actions: {fetchTimeline},
            filters: {dates: {startDate}},
            suggestedRoomIds,
        } = this.props;
        const lazyScroll = {
            hasMore: hasMoreTimelineData,
            loadMore: fetchTimeline,
            isFetching: fetchingTimeline,
        };
        return (
            <BookingTimelineComponent lazyScroll={lazyScroll}
                                      isFetching={fetchingTimeline}
                                      pushState={pushState}
                                      minHour={minHour}
                                      maxHour={maxHour}
                                      availability={availability}
                                      dateRange={dateRange}
                                      recurrenceType={recurrenceType}
                                      defaultDate={startDate}
                                      allowSingleRoom={!suggestedRoomIds.length}
                                      showEmptyMessage={false} />
        );
    }
}

export default connect(
    state => ({
        availability: bookRoomSelectors.getTimelineAvailability(state),
        dateRange: bookRoomSelectors.getTimelineDateRange(state),
        fetchingTimeline: bookRoomSelectors.isFetchingTimeline(state),
        roomIds: bookRoomSelectors.getSearchResultIds(state),
        suggestedRoomIds: bookRoomSelectors.getSuggestedRoomIds(state),
        hasMoreTimelineData: bookRoomSelectors.hasMoreTimelineData(state),
        recurrenceType: state.bookRoom.filters.recurrence.type,
        queryString: stateToQueryString(state.bookRoom, queryStringSerializer),
        filters: bookRoomSelectors.getFilters(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            initTimeline: bookRoomActions.initTimeline,
            fetchTimeline: bookRoomActions.fetchTimeline,
            addTimelineRooms: bookRoomActions.addTimelineRooms,
            fetchRoomSuggestions: bookRoomActions.fetchRoomSuggestions,
        }, dispatch),
        dispatch
    }),
    pushStateMergeProps
)(BookingTimeline);
