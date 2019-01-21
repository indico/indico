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
import {Button, Checkbox, Grid, Icon, Message, Modal, Segment} from 'semantic-ui-react';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import camelizeKeys from 'indico/utils/camelize';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {serializeDate, serializeTime} from 'indico/utils/date';
import {ajax as ajaxFilterRules} from '../roomSearch/serializers';
import {selectors as userSelectors} from '../user';
import {getRecurrenceInfo, preProcessParameters, serializeRecurrenceInfo} from '../../util';
import RoomBasicDetails from '../../components/RoomBasicDetails';
import BookingEditForm from './BookingEditForm';
import BookingEditCalendar from './BookingEditCalendar';
import * as bookingsActions from './actions';
import * as bookingsSelectors from './selectors';

import './BookingEdit.module.scss';


class BookingEdit extends React.Component {
    static propTypes = {
        user: PropTypes.object.isRequired,
        actionButtons: PropTypes.func,
        onSubmit: PropTypes.func.isRequired,
        onClose: PropTypes.func,
        booking: PropTypes.object.isRequired,
        isOngoingBooking: PropTypes.bool.isRequired,
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
            numberOfConflicts: 0,
            numberOfCandidates: 0,
            datePeriodChanged: false,
            calendars: {
                currentBooking: {
                    isFetching: false,
                    data: {
                        bookings: {...occurrences.bookings},
                        cancellations: {...occurrences.cancellations},
                        rejections: {...occurrences.rejections},
                        other: {...occurrences.otherBookings},
                        pendingCancelations: {},
                        candidates: {},
                        conflicts: {}
                    },
                    dateRange,
                },
                newBooking: null, // available only when splitting an ongoing booking
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

    getNumberOfOccurrenceByType = (data, type) => {
        if (!(type in data)) {
            return 0;
        } else if (type === 'conflicts') {
            return Object.values(data.conflicts).filter(conflicts => conflicts.length !== 0).length;
        }
        return Object.values(data[type]).reduce((acc, cur) => acc + (cur.length ? 1 : 0), 0);
    };

    resetCalendarStateOnUpdate = (datePeriodChanged) => {
        const {isOngoingBooking} = this.props;
        const {calendars: {currentBooking, newBooking}} = this.state;
        const newState = {
            datePeriodChanged,
            calendars: {currentBooking},
            numberOfCandidates: 0,
            numberOfConflicts: 0,
            skipConflicts: false,
        };

        if (isOngoingBooking && datePeriodChanged) {
            newState.calendars.newBooking = {
                ...(newBooking || {}),
                data: {
                    candidates: {},
                    conflicts: {},
                },
                isFetching: true,
                dateRange: [],
            };
        } else {
            newState.calendars.currentBooking = {
                ...currentBooking,
                data: {
                    ...currentBooking.data,
                    candidates: {},
                    conflicts: {},
                },
                isFetching: true,
            };
            newState.calendars.newBooking = null;
        }

        this.setState(newState);
    };

    getUpdatedCalendars = (dateRange, newDateRange, candidates, conflicts) => {
        const {isOngoingBooking} = this.props;
        const {datePeriodChanged, calendars: {currentBooking}} = this.state;
        let newCalendars;

        if (isOngoingBooking && datePeriodChanged) {
            const {data: {bookings}} = currentBooking;
            const pendingCancelations = _.fromPairs(_.compact(Object.entries(bookings).map(([day, data]) => {
                return moment().isAfter(day, 'day') ? [day, data] : null;
            })));

            newCalendars = {
                currentBooking: {
                    ...currentBooking,
                    isFetching: false,
                    data: {
                        ...currentBooking.data,
                        pendingCancelations,
                    },
                    dateRange: dateRange.filter((dt) => moment().isAfter(dt, 'day')),
                },
                newBooking: {
                    isFetching: false,
                    data: {
                        ...currentBooking.data,
                        bookings: {},
                        pendingCancelations: {},
                        cancellations: {},
                        candidates,
                        conflicts,
                    },
                    dateRange: newDateRange,
                }
            };
        } else {
            newCalendars = {
                currentBooking: {
                    ...currentBooking,
                    isFetching: false,
                    data: {
                        ...currentBooking.data,
                        candidates,
                        conflicts,
                        pendingCancelations: {},
                    },
                    dateRange: _.uniq([...dateRange, ...newDateRange]).sort(),
                }
            };
        }

        return newCalendars;
    };

    updateBookingCalendar = async (dates, timeSlot, recurrence) => {
        const {
            isOngoingBooking,
            booking: {room: {id}, dateRange, id: bookingId, startDt, endDt, repetition}
        } = this.props;
        const {calendars: {currentBooking}} = this.state;
        const {startTime: newStartTime, endTime: newEndTime} = timeSlot;
        const datePeriodChanged = (
            serializeTime(startDt) !== newStartTime ||
            serializeTime(endDt) !== newEndTime ||
            !_.isEqual(getRecurrenceInfo(repetition), recurrence)
        );

        const newDates = {...dates};
        if (isOngoingBooking && datePeriodChanged) {
            const today = moment();
            const {startDate} = dates;
            newDates.startDate = today.isBefore(startDate, 'day') ? serializeDate(startDate) : serializeDate(today);
        }

        this.resetCalendarStateOnUpdate(datePeriodChanged);

        const params = preProcessParameters({timeSlot, recurrence, dates: newDates}, ajaxFilterRules);
        let response, candidates;
        try {
            response = await indicoAxios.post(
                fetchTimelineURL(),
                {room_ids: [id], skip_conflicts_with: bookingId},
                {params},
            );
        } catch (error) {
            handleAxiosError(error);
            return;
        }

        const {availability, dateRange: newDateRange} = camelizeKeys(response.data);
        const availabilityData = availability[0][1];

        if (_.isEqual(newDateRange, dateRange)) {
            if (datePeriodChanged) {
                candidates = availabilityData.candidates;
            } else {
                candidates = {};
            }
        } else {
            candidates = availabilityData.candidates;
        }

        // Filter out rejections and cancellations from candidates
        const {data: {cancellations, rejections}} = currentBooking;
        candidates = _.pick(candidates, newDateRange.filter(date => !(date in rejections) && !(date in cancellations)));

        this.setState({
            calendars: this.getUpdatedCalendars(dateRange, newDateRange, candidates, availabilityData.conflicts),
            numberOfConflicts: availabilityData.numConflicts,
            numberOfCandidates: availabilityData.numDaysAvailable
        });
    };

    renderBookingEditModal = (fprops) => {
        const {submitting, submitSucceeded, hasValidationErrors, pristine} = fprops;
        const {booking, onClose, actionButtons, isOngoingBooking} = this.props;
        const {room} = booking;
        const {skipConflicts, datePeriodChanged, calendars, numberOfConflicts, numberOfCandidates} = this.state;
        const conflictingBooking = numberOfConflicts > 0 && !skipConflicts;
        const submitBlocked = submitting || submitSucceeded || hasValidationErrors || pristine || conflictingBooking;

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
                            {isOngoingBooking && (
                                <Message color="blue" size="mini" styleName="ongoing-booking-info" icon>
                                    <Icon name="play" />
                                    <Translate>
                                        This booking has already started.
                                    </Translate>
                                </Message>
                            )}
                            <BookingEditForm booking={booking}
                                             formProps={fprops}
                                             onBookingPeriodChange={this.updateBookingCalendar} />
                        </Grid.Column>
                        <Grid.Column stretched>
                            <BookingEditCalendar calendars={calendars}
                                                 booking={booking}
                                                 numberOfCandidates={numberOfCandidates}
                                                 numberOfConflicts={numberOfConflicts}
                                                 datePeriodChanged={datePeriodChanged} />
                            {this.renderConflictsMessage()}
                        </Grid.Column>
                    </Grid>
                </Modal.Content>
                <Modal.Actions>
                    <Button type="submit"
                            form="booking-edit-form"
                            disabled={submitBlocked}
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

    renderConflictsMessage = () => {
        const {skipConflicts, numberOfConflicts, numberOfCandidates} = this.state;

        if (!numberOfConflicts) {
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
                        <PluralTranslate count={numberOfConflicts}>
                            <Singular>
                                Your new booking conflicts with another one.
                            </Singular>
                            <Plural>
                                <Param name="count" value={numberOfConflicts} /> occurrences of your
                                booking are unavailable due to conflicts.
                            </Plural>
                        </PluralTranslate>
                    </Message.Content>
                </Message>
                {numberOfCandidates > 0 && numberOfConflicts > 0 && (
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
    (state, {booking: {id}}) => ({
        user: userSelectors.getUserInfo(state),
        isOngoingBooking: bookingsSelectors.isOngoingBooking(state, {bookingId: id}),
    }),
    (dispatch) => ({
        actions: bindActionCreators({
            updateBooking: bookingsActions.updateBooking,
        }, dispatch),
    })
)(BookingEdit);
