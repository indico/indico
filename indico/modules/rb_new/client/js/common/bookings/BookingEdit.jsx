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

import fetchTimelineURL from 'indico-url:rooms_new.timeline';

import _ from 'lodash';
import moment from 'moment';
import React from 'react';
import PropTypes from 'prop-types';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Form as FinalForm} from 'react-final-form';
import {Button, Checkbox, Grid, Header, Icon, Label, Message, Modal, Popup, Segment} from 'semantic-ui-react';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import camelizeKeys from 'indico/utils/camelize';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {serializeDate, serializeTime} from 'indico/utils/date';
import {ajax as ajaxFilterRules} from '../roomSearch/serializers';
import {DailyTimelineContent, TimelineLegend} from '../timeline';
import {selectors as userSelectors} from '../user';
import {getRecurrenceInfo, preProcessParameters, serializeRecurrenceInfo} from '../../util';
import RoomBasicDetails from '../../components/RoomBasicDetails';
import BookingEditForm from './BookingEditForm';
import * as bookRoomActions from './actions';

import './BookingEdit.module.scss';


class BookingEdit extends React.Component {
    static propTypes = {
        user: PropTypes.object.isRequired,
        actionButtons: PropTypes.func,
        onSubmit: PropTypes.func.isRequired,
        onClose: PropTypes.func,
        booking: PropTypes.object.isRequired,
        actions: PropTypes.exact({
            updateBooking: PropTypes.func.isRequired,
        }).isRequired,
    };

    static defaultProps = {
        actionButtons: () => {},
        onClose: () => {},
    };

    constructor(props) {
        super(props);

        const {booking: {occurrences, dateRange}} = props;
        this.state = {
            skipConflicts: false,
            calendar: {
                isFetching: false,
                data: {
                    bookings: occurrences.bookings,
                    cancellations: occurrences.cancellations,
                    rejections: occurrences.rejections,
                    other: occurrences.otherBookings,
                    candidates: {},
                    conflicts: {}
                },
                dateRange,
            },
        };
    }

    get formInitialValues() {
        const {user: sessionUser, booking: {repetition, startDt, endDt, bookedForUser, bookingReason}} = this.props;
        const recurrence = getRecurrenceInfo(repetition);
        const isSingleBooking = recurrence.type === 'single';
        const dates = {startDate: serializeDate(startDt), endDate: isSingleBooking ? null : serializeDate(endDt)};
        const timeSlot = {startTime: serializeTime(startDt), endTime: serializeTime(endDt)};
        const usage = bookedForUser.id === sessionUser.id ? 'myself' : 'someone';
        const user = {...bookedForUser, isGroup: false};

        return {
            recurrence,
            dates,
            timeSlot,
            usage,
            user,
            reason: bookingReason
        };
    }

    getNumberOfOccurrenceByType = (type) => {
        const {calendar: {data}} = this.state;
        if (!(type in data)) {
            return 0;
        }
        return Object.values(data[type]).reduce((acc, cur) => acc + (cur.length ? 1 : 0), 0);
    };

    get numberOfConflicts() {
        return this.getNumberOfOccurrenceByType('conflicts');
    }

    get numberOfCandidates() {
        return this.getNumberOfOccurrenceByType('candidates');
    }

    get numberOfOccurrences() {
        return this.getNumberOfOccurrenceByType('bookings');
    }

    updateBookingCalendar = async (dates, timeSlot, recurrence) => {
        const {booking: {room: {id}, dateRange, id: bookingId}} = this.props;
        const {calendar} = this.state;
        const params = preProcessParameters({dates, timeSlot, recurrence}, ajaxFilterRules);

        this.setState({
            calendar: {
                ...calendar,
                data: {...calendar.data, candidates: {}, conflicts: {}},
                isFetching: true,
            }
        });

        let response, candidates;
        try {
            response = await indicoAxios.post(fetchTimelineURL(), {room_ids: [id]}, {params});
        } catch (error) {
            handleAxiosError(error);
            return;
        }

        const {availability, dateRange: newDateRange} = camelizeKeys(response.data);
        const availabilityData = availability[0][1];
        const conflicts = _.fromPairs(newDateRange.map((day) => {
            const allConflicts = availabilityData.conflicts[day] || [];
            if (day in calendar.data.cancellations || day in calendar.data.rejections) {
                return [day, []];
            }
            return [day, allConflicts.filter((c) => !c.reservation || c.reservation.id !== bookingId)];
        }));

        if (_.isEqual(newDateRange, dateRange)) {
            candidates = newDateRange.reduce((accum, day) => {
                if (!(day in calendar.data.bookings)) {
                    accum[day] = availabilityData.candidates[day];
                } else {
                    const dayBookings = calendar.data.bookings[day];
                    if (!dayBookings.length) {
                        accum[day] = availabilityData.candidates[day];
                    } else {
                        accum[day] = availabilityData.candidates[day].filter((candidate, index) => {
                            const booking = dayBookings[index];
                            const isSameStart = moment(candidate.startDt).isSame(moment(booking.startDt));
                            const isSameEnd = moment(candidate.endDt).isSame(moment(booking.endDt));
                            return !isSameStart || !isSameEnd;
                        });
                    }
                }
                return accum;
            }, {});
        } else {
            candidates = availabilityData.candidates;
        }

        /* Filter out rejections and cancellations from candidates */
        const {data: {cancellations, rejections}} = calendar;
        const candidatesDateRange = newDateRange.filter(date => !(date in rejections) && !(date in cancellations));
        candidates = _.pick(candidates, candidatesDateRange);

        this.setState({
            calendar: {
                isFetching: false,
                data: {
                    ...calendar.data,
                    candidates,
                    conflicts
                },
                dateRange: _.uniq([...dateRange, ...newDateRange]).sort(),
            },
        });
    };

    renderBookingEditModal = (fprops) => {
        const {submitting, submitSucceeded, hasValidationErrors, pristine} = fprops;
        const {booking, onClose, actionButtons} = this.props;
        const {room} = booking;
        const {skipConflicts} = this.state;
        const submitBlocked = submitting || submitSucceeded || hasValidationErrors || pristine;
        const conflictingBooking = (
            (this.numberOfCandidates !== 0 && this.numberOfCandidates === this.numberOfConflicts) ||
            (this.numberOfConflicts > 0 && !skipConflicts)
        );

        return (
            <Modal size="large" onClose={onClose} closeIcon open>
                <Modal.Header styleName="booking-edit-modal-header">
                    <Translate>Edit a booking</Translate>
                    {actionButtons()}
                </Modal.Header>
                <Modal.Content>
                    <Grid columns={2}>
                        <Grid.Column>
                            <RoomBasicDetails room={room} />
                            <BookingEditForm booking={booking} formProps={fprops}
                                             onBookingPeriodChange={this.updateBookingCalendar} />
                        </Grid.Column>
                        <Grid.Column stretched>
                            {this.renderBookingCalendar()}
                            {this.renderConflictsMessage()}
                        </Grid.Column>
                    </Grid>
                </Modal.Content>
                <Modal.Actions>
                    <Button type="submit"
                            form="booking-edit-form"
                            disabled={submitBlocked || conflictingBooking}
                            primary>
                        <Translate>Save changes</Translate>
                    </Button>
                    <Button type="button" onClick={onClose}>
                        <Translate>Close</Translate>
                    </Button>
                </Modal.Actions>
            </Modal>
        );
    };

    renderBookingCalendar = () => {
        const {calendar: {isFetching, data: av, dateRange}} = this.state;
        const {booking: {room}} = this.props;
        const legendLabels = [
            {label: Translate.string('Current booking'), color: 'orange', style: 'booking'},
            {label: Translate.string('Cancelled occurrences'), style: 'cancellation'},
            {label: Translate.string('Rejected occurrences'), style: 'rejection'},
            {label: Translate.string('Other bookings'), style: 'other'},
            {label: Translate.string('New booking'), color: 'green', style: 'new-booking'},
            {label: Translate.string('Conflicts with new booking'), color: 'red', style: 'conflict'},
        ];
        const serializeRow = (day) => {
            return {
                availability: {
                    bookings: av.bookings[day] || [],
                    cancellations: av.cancellations[day] || [],
                    rejections: av.rejections[day] || [],
                    other: av.other[day] || [],
                    candidates: (av.candidates[day] || []).map(candidate => ({...candidate, bookable: false})),
                    conflicts: av.conflicts[day] || [],
                },
                label: moment(day).format('L'),
                key: day,
                room,
            };
        };
        let numNewCandidates;
        if (this.numberOfConflicts) {
            numNewCandidates = this.numberOfCandidates - this.numberOfConflicts;
        } else {
            numNewCandidates = this.numberOfCandidates;
        }

        return (
            <div styleName="booking-calendar">
                <Header className="legend-header">
                    <span>
                        <Translate>Occurrences</Translate>
                    </span>
                    <Popup trigger={<Icon name="info circle" className="legend-info-icon" />}
                           position="right center"
                           content={<TimelineLegend labels={legendLabels} compact />} />
                    <Label.Group styleName="occurrence-count">
                        <Popup trigger={<Label color="blue" size="tiny" content={this.numberOfOccurrences} circular />}
                               position="bottom center"
                               on="hover">
                            <Translate>
                                Number of occurrences for this booking
                            </Translate>
                        </Popup>
                        {numNewCandidates > 0 && (
                            <>
                                {' → '}
                                <Popup trigger={<Label color="grey" size="tiny" content={numNewCandidates}
                                                       circular />}
                                       position="bottom center"
                                       on="hover">
                                    <Translate>
                                        Number of occurrences for this booking after changes
                                    </Translate>
                                </Popup>
                            </>
                        )}
                    </Label.Group>
                </Header>
                <DailyTimelineContent rows={isFetching ? [] : dateRange.map(serializeRow)}
                                      fixedHeight={dateRange.length > 1 ? '100%' : null}
                                      isLoading={isFetching} />
            </div>
        );
    };

    renderConflictsMessage = () => {
        const {skipConflicts} = this.state;

        if (!this.numberOfConflicts) {
            return null;
        }

        return (
            <div styleName="booking-conflicts-info">
                <Message color="yellow" attached icon>
                    <Icon name="warning circle" />
                    <Message.Content>
                        <Message.Header>
                            <Translate>Conflicts with new booking</Translate>
                        </Message.Header>
                        <PluralTranslate count={this.numberOfConflicts}>
                            <Singular>
                                Your new booking conflicts with another one.
                            </Singular>
                            <Plural>
                                <Param name="count" value={this.numberOfConflicts} /> occurrences of your
                                new booking might conflict with existing bookings.
                            </Plural>
                        </PluralTranslate>
                    </Message.Content>
                </Message>
                {this.numberOfCandidates > this.numberOfConflicts && (
                    <Segment attached="bottom">
                        <Checkbox toggle
                                  defaultChecked={skipConflicts}
                                  label={Translate.string('I understand, please skip any days with conflicting ' +
                                                          'occurrences.')}
                                  onChange={(__, {checked}) => {
                                      this.setState({
                                          skipConflicts: checked
                                      });
                                  }} />
                    </Segment>
                )}
            </div>
        );
    };

    updateBooking = async (data) => {
        const {dates: {startDate, endDate}, timeSlot: {startTime, endTime}, usage, user, reason, recurrence} = data;
        const {actions: {updateBooking}, booking: {id, room: {id: roomId}}, onSubmit} = this.props;
        const [repeatFrequency, repeatInterval] = serializeRecurrenceInfo(recurrence);
        const params = {
            start_dt: `${startDate} ${startTime}`,
            end_dt: `${endDate ? endDate : startDate} ${endTime}`,
            repeat_frequency: repeatFrequency,
            repeat_interval: repeatInterval,
            room_id: roomId,
            user_id: usage === 'myself' ? undefined : user.id,
            booking_reason: reason,
        };

        const rv = await updateBooking(id, params);
        if (rv.error) {
            return rv.error;
        } else {
            onSubmit();
        }
    };

    render() {
        return (
            <FinalForm onSubmit={this.updateBooking}
                       render={this.renderBookingEditModal}
                       initialValues={this.formInitialValues}
                       subscription={{
                           submitting: true,
                           submitSucceeded: true,
                           hasValidationErrors: true,
                           pristine: true,
                           values: true,
                       }}
                       keepDirtyOnReinitialize />
        );
    }
}


export default connect(
    (state) => ({
        user: userSelectors.getUserInfo(state),
    }),
    (dispatch) => ({
        actions: bindActionCreators({
            updateBooking: bookRoomActions.updateBooking,
        }, dispatch),
    })
)(BookingEdit);
