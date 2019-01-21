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
import {connect} from 'react-redux';
import {Header, Icon, List, Message, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';
import {DailyTimelineContent, TimelineLegend} from '../timeline';
import OccurrencesCounter from './OccurrencesCounter';
import * as bookingsSelectors from './selectors';

import './BookingEditCalendar.module.scss';


class BookingEditCalendar extends React.Component {
    static propTypes = {
        booking: PropTypes.object.isRequired,
        isOngoingBooking: PropTypes.bool.isRequired,
        numberOfBookingOccurrences: PropTypes.number.isRequired,
        numberOfCandidates: PropTypes.number,
        datePeriodChanged: PropTypes.bool.isRequired,
        calendars: PropTypes.object.isRequired,
    };

    static defaultProps = {
        numberOfCandidates: 0,
    };

    static legendLabels = [
        {label: Translate.string('Current booking'), color: 'orange', style: 'booking'},
        {label: Translate.string('Cancelled occurrences'), style: 'cancellation'},
        {label: Translate.string('Pending cancellations'), style: 'pending-cancellation'},
        {label: Translate.string('Rejected occurrences'), style: 'rejection'},
        {label: Translate.string('Other bookings'), style: 'other'},
        {label: Translate.string('New booking'), color: 'green', style: 'new-booking'},
        {label: Translate.string('Conflicts with new booking'), color: 'red', style: 'conflict'},
    ];

    serializeRow = (data) => {
        const {booking: {room}} = this.props;
        return (day) => ({
            availability: {
                bookings: data.bookings[day] || [],
                cancellations: data.cancellations[day] || [],
                rejections: data.rejections[day] || [],
                other: data.other[day] || [],
                candidates: (data.candidates[day] || []).map(candidate => ({...candidate, bookable: false})),
                conflicts: data.conflicts[day] || [],
                pendingCancelations: data.pendingCancelations[day] || [],
            },
            label: serializeDate(day, 'L'),
            key: day,
            room,
        });
    };

    getCalendarData = (calendar) => {
        const {isFetching, dateRange, data} = calendar;
        return isFetching ? [] : dateRange.map(this.serializeRow(data));
    };

    renderNumberOfOccurrences = () => {
        const {
            calendars: {currentBooking: {data: {pendingCancelations}}}, numberOfBookingOccurrences, numberOfCandidates,
        } = this.props;
        const numBookingPastOccurrences = Object.keys(pendingCancelations).length;

        return (
            <OccurrencesCounter bookingsCount={numberOfBookingOccurrences}
                                newBookingsCount={numberOfCandidates}
                                pastBookingsCount={numBookingPastOccurrences} />
        );
    };

    render() {
        const {datePeriodChanged, isOngoingBooking, calendars: {currentBooking, newBooking}} = this.props;
        return (
            <div styleName="booking-calendar">
                <Header className="legend-header">
                    <span>
                        <Translate>Occurrences</Translate>
                    </span>
                    <Popup trigger={<Icon name="info circle" className="legend-info-icon" />}
                           position="right center"
                           content={<TimelineLegend labels={BookingEditCalendar.legendLabels} compact />} />
                    {this.renderNumberOfOccurrences()}
                </Header>
                {isOngoingBooking && datePeriodChanged && (
                    <Message styleName="ongoing-booking-explanation" color="green" icon>
                        <Icon name="code branch" />
                        <Message.Content>
                            <Translate>
                                Your booking has already started and will be split into:
                            </Translate>
                            <List bulleted>
                                <List.Item>
                                    <Translate>
                                        the original booking, which will be shortened;
                                    </Translate>
                                </List.Item>
                                <List.Item>
                                    <Translate>
                                        a new booking, which will take into account the updated time information.
                                    </Translate>
                                </List.Item>
                            </List>
                        </Message.Content>
                    </Message>
                )}
                <div styleName="calendars">
                    <div styleName="original-booking">
                        <DailyTimelineContent rows={this.getCalendarData(currentBooking)}
                                              maxHour={24}
                                              renderHeader={isOngoingBooking && datePeriodChanged ? () => (
                                                  <Header as="h3" color="orange" styleName="original-booking-header">
                                                      <Translate>Original booking</Translate>
                                                  </Header>
                                              ) : null}
                                              isLoading={currentBooking.isFetching}
                                              fixedHeight={currentBooking.dateRange.length > 0 ? '100%' : null} />
                    </div>
                    {newBooking && (
                        <div styleName="new-booking">
                            <DailyTimelineContent rows={this.getCalendarData(newBooking)}
                                                  maxHour={24}
                                                  renderHeader={() => (
                                                      <Header as="h3" color="green" styleName="new-booking-header">
                                                          <Translate>New booking</Translate>
                                                      </Header>
                                                  )}
                                                  isLoading={newBooking.isFetching}
                                                  fixedHeight={newBooking.dateRange.length > 0 ? '100%' : null} />
                        </div>
                    )}
                </div>
            </div>
        );
    }
}

export default connect(
    (state, {booking: {id}}) => ({
        isOngoingBooking: bookingsSelectors.isOngoingBooking(state, {bookingId: id}),
        numberOfBookingOccurrences: bookingsSelectors.getNumberOfBookingOccurrences(state, {bookingId: id}),
    }),
)(BookingEditCalendar);
