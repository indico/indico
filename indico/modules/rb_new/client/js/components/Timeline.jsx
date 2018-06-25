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
import {Button, Container, Label, Loader, Message, Segment} from 'semantic-ui-react';
import DatePicker from 'rc-calendar/lib/Picker';
import Calendar from 'rc-calendar';
import {Translate} from 'indico/react/i18n';
import TimelineContent from './TimelineContent';

import './Timeline.module.scss';


const DATE_FORMAT = 'YYYY-MM-DD';
const _toMoment = (date) => moment(date, DATE_FORMAT);


export default class Timeline extends React.Component {
    static propTypes = {
        minHour: PropTypes.number.isRequired,
        maxHour: PropTypes.number.isRequired,
        step: PropTypes.number,
        dateRange: PropTypes.array.isRequired,
        availability: PropTypes.object.isRequired,
        isFetching: PropTypes.bool.isRequired,
        resetBookingState: PropTypes.func.isRequired,
        recurrenceType: PropTypes.string.isRequired,
        pushState: PropTypes.func.isRequired,
        isFetchingRooms: PropTypes.bool.isRequired,
    };

    static defaultProps = {
        step: 2
    };

    static getDerivedStateFromProps(props, state) {
        const activeDate = _toMoment(props.dateRange[0]);
        if (!_.isEmpty(props.dateRange) && activeDate !== state.activeDate) {
            return {...state, activeDate};
        } else {
            return state;
        }
    }

    constructor(props) {
        super(props);

        const {dateRange} = this.props;
        this.state = {
            activeDate: _toMoment(dateRange[0])
        };
    }

    changeSelectedDate = (mode) => {
        const {dateRange} = this.props;
        const {activeDate} = this.state;
        const index = dateRange.findIndex((dt) => _toMoment(dt).isSame(activeDate)) + (mode === 'next' ? 1 : -1);

        this.setState({activeDate: _toMoment(dateRange[index])});
    };

    isDateWithinTimelineRange = (date) => {
        const {dateRange} = this.props;
        return dateRange.filter((dt) => _toMoment(dt).isSame(date, 'day')).length !== 0;
    };

    onSelect = (date) => {
        const {dateRange} = this.props;
        const startDate = _toMoment(dateRange[0]);
        const endDate = _toMoment(dateRange[dateRange.length - 1]);

        if (date.isBefore(_toMoment(startDate)) || date.isAfter(_toMoment(endDate))) {
            return;
        } else if (this.isDateWithinTimelineRange(date)) {
            this.setState({activeDate: date});
        }
    };

    renderContent = () => {
        const {availability, isFetching, isFetchingRooms} = this.props;
        if (isFetching || isFetchingRooms) {
            return <Loader active />;
        } else if (!_.isEmpty(availability)) {
            return this.renderTimeline();
        } else {
            return this.renderEmptyMessage();
        }
    };

    calendarDisabledDate = (date) => {
        if (!date) {
            return false;
        }
        return !this.isDateWithinTimelineRange(date);
    };

    renderTimelineLegend = () => {
        const {activeDate} = this.state;
        const {dateRange, availability} = this.props;
        let currentDate = activeDate;
        const startDate = _toMoment(dateRange[0]);
        const endDate = _toMoment(dateRange[dateRange.length - 1]);
        if (!this.isDateWithinTimelineRange(currentDate)) {
            currentDate = _toMoment(startDate);
            this.setState({activeDate: currentDate});
        }
        const calendar = <Calendar disabledDate={this.calendarDisabledDate} onChange={this.onSelect} />;
        return (
            <Segment styleName="legend" basic>
                <Label.Group as="span" size="large" styleName="labels">
                    <Label color="green">{Translate.string('Available')}</Label>
                    <Label color="orange">{Translate.string('Booked')}</Label>
                    <Label styleName="pre-booking">{Translate.string('Pre-Booking')}</Label>
                    <Label color="red">{Translate.string('Conflict')}</Label>
                    <Label styleName="pre-booking-conflict">{Translate.string('Conflict with Pre-Booking')}</Label>
                    <Label styleName="blocking">{Translate.string('Blocked')}</Label>
                    <Label styleName="unavailable">{Translate.string('Not available')}</Label>
                </Label.Group>
                {Object.keys(availability).length > 1 && (
                    <Button.Group floated="right" size="small">
                        <Button icon="left arrow"
                                onClick={() => this.changeSelectedDate('prev')}
                                disabled={moment(activeDate).subtract(1, 'day').isBefore(startDate)} />
                        <DatePicker calendar={calendar}>
                            {
                                () => (
                                    <Button primary>
                                        {activeDate.format(DATE_FORMAT)}
                                    </Button>
                                )
                            }
                        </DatePicker>
                        <Button icon="right arrow"
                                onClick={() => this.changeSelectedDate('next')}
                                disabled={moment(activeDate).add(1, 'day').isAfter(endDate)} />
                    </Button.Group>
                )}
            </Segment>
        );
    };

    renderTimeline = () => {
        const {activeDate} = this.state;
        const {minHour, maxHour, step, availability, recurrenceType, dateRange} = this.props;
        const hourSeries = _.range(minHour, maxHour + step, step);

        let rows = [];
        if (Object.keys(availability).length === 1) {
            const roomId = Object.keys(availability)[0];
            const roomAvailability = availability[roomId];
            const room = roomAvailability.room;

            rows = dateRange.map((dt) => {
                const av = {
                    candidates: roomAvailability.candidates[dt].map((cand) => ({...cand, bookable: true})) || [],
                    preBookings: roomAvailability.pre_bookings[dt] || [],
                    bookings: roomAvailability.bookings[dt] || [],
                    conflicts: roomAvailability.conflicts[dt] || [],
                    preConflicts: roomAvailability.pre_conflicts[dt] || [],
                    blockings: roomAvailability.blockings[dt] || []
                };
                return {availability: av, label: dt, conflictIndicator: true, id: dt, room};
            });
        } else {
            const dt = activeDate.format('YYYY-MM-DD');
            rows = Object.values(availability).map((roomAvailability) => {
                const av = {
                    candidates: roomAvailability.candidates[dt].map((cand) => ({...cand, bookable: true})) || [],
                    preBookings: roomAvailability.pre_bookings[dt] || [],
                    bookings: roomAvailability.bookings[dt] || [],
                    conflicts: roomAvailability.conflicts[dt] || [],
                    preConflicts: roomAvailability.pre_conflicts[dt] || [],
                    blockings: roomAvailability.blockings[dt] || []
                };

                const room = roomAvailability.room;
                return {availability: av, label: room.full_name, conflictIndicator: true, id: room.id, room};
            });
        }

        return (
            <>
                {this.renderTimelineLegend()}
                <div styleName="timeline">
                    <TimelineContent rows={rows}
                                     hourSeries={hourSeries}
                                     recurrenceType={recurrenceType}
                                     openModal={this.openBookingModal} />
                </div>
            </>
        );
    };


    renderEmptyMessage = () => {
        return (
            <Message warning>
                <Translate>
                    There are no rooms matching the criteria.
                </Translate>
            </Message>
        );
    };

    openBookingModal = (room) => {
        const {pushState} = this.props;
        pushState(`/book/${room.id}/confirm`, true);
    };

    closeBookingModal = () => {
        const {resetBookingState, pushState} = this.props;
        resetBookingState();
        pushState(`/book`, true);
    };

    render() {
        return (
            <Container>
                {this.renderContent()}
            </Container>
        );
    }
}
