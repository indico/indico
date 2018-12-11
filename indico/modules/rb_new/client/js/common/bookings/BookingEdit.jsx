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
import {camelizeKeys} from 'indico/utils/case';
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
        isAdminOverrideEnabled: PropTypes.bool.isRequired,
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
            numberOfConflicts: null,
            numberOfCandidates: null,
            shouldSplit: false,
            calendars: {
                currentBooking: {
                    isFetching: false,
                    data: {
                        bookings: {...occurrences.bookings},
                        cancellations: {...occurrences.cancellations},
                        rejections: {...occurrences.rejections},
                        other: {...occurrences.otherBookings},
                        pendingCancellations: {},
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

    resetCalendarStateOnUpdate = (shouldSplit) => {
        const {isOngoingBooking} = this.props;
        const {calendars: {currentBooking, newBooking}} = this.state;
        const newState = {
            shouldSplit,
            calendars: {currentBooking},
            numberOfCandidates: null,
            numberOfConflicts: null,
            skipConflicts: false,
        };

        if (isOngoingBooking && shouldSplit) {
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
        const {shouldSplit, calendars: {currentBooking}} = this.state;

        if (isOngoingBooking && shouldSplit) {
            const {data: {bookings}} = currentBooking;
            const pendingCancellations = _.fromPairs(_.compact(Object.entries(bookings).map(([day, data]) => {
                return moment().isSameOrBefore(day, 'day') ? [day, data] : null;
            })));

            return {
                currentBooking: {
                    ...currentBooking,
                    isFetching: false,
                    data: {
                        ...currentBooking.data,
                        pendingCancellations,
                    },
                },
                newBooking: {
                    isFetching: false,
                    data: {
                        ...currentBooking.data,
                        bookings: {},
                        pendingCancellations: {},
                        cancellations: {},
                        candidates,
                        conflicts,
                    },
                    dateRange: newDateRange,
                }
            };
        } else {
            return {
                currentBooking: {
                    ...currentBooking,
                    isFetching: false,
                    data: {
                        ...currentBooking.data,
                        candidates,
                        conflicts,
                        pendingCancellations: {},
                    },
                    dateRange: _.uniq([...dateRange, ...newDateRange]).sort(),
                }
            };
        }
    };

    updateBookingCalendar = async (dates, timeSlot, recurrence) => {
        const {
            isOngoingBooking,
            isAdminOverrideEnabled,
            booking: {room: {id}, dateRange, id: bookingId, startDt, endDt, repetition},
        } = this.props;
        const {calendars: {currentBooking}} = this.state;
        const {startTime: newStartTime, endTime: newEndTime} = timeSlot;
        const shouldSplit = (
            serializeTime(startDt) !== newStartTime ||
            serializeTime(endDt) !== newEndTime ||
            !_.isEqual(getRecurrenceInfo(repetition), recurrence)
        );
        const datePeriodChanged = (
            !_.isEqual(getRecurrenceInfo(repetition), recurrence) ||
            !_.isEqual([serializeTime(startDt), serializeTime(endDt)], [newStartTime, newEndTime]) ||
            !_.isEqual([serializeDate(startDt), serializeDate(endDt)], [dates.startDate, dates.endDate])
        );

        const newDates = {...dates};
        if (isOngoingBooking && shouldSplit) {
            const today = moment();
            const {startDate} = dates;
            newDates.startDate = today.isBefore(startDate, 'day') ? serializeDate(startDate) : serializeDate(today);
        }

        this.resetCalendarStateOnUpdate(shouldSplit);

        const params = preProcessParameters({timeSlot, recurrence, dates: newDates}, ajaxFilterRules);
        if (isAdminOverrideEnabled) {
            params.admin_override_enabled = true;
        }
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
            numberOfCandidates: datePeriodChanged ? availabilityData.numDaysAvailable : null,
        });
    };

    renderBookingEditModal = (fprops) => {
        const {submitting, submitSucceeded, hasValidationErrors, pristine} = fprops;
        const {booking, onClose, actionButtons, isOngoingBooking} = this.props;
        const {room} = booking;
        const {skipConflicts, shouldSplit, calendars, numberOfConflicts, numberOfCandidates} = this.state;
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
                                <Message color="blue" styleName="ongoing-booking-info" icon>
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
                                                 shouldSplit={shouldSplit && isOngoingBooking} />
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
        isAdminOverrideEnabled: userSelectors.isUserAdminOverrideEnabled(state),
    }),
    (dispatch) => ({
        actions: bindActionCreators({
            updateBooking: bookingsActions.updateBooking,
        }, dispatch),
    })
)(BookingEdit);
