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
import {Button, Checkbox, Grid, Header, Icon, Label, List, Message, Modal, Popup, Segment} from 'semantic-ui-react';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import camelizeKeys from 'indico/utils/camelize';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {toClasses} from 'indico/react/util';
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
            timeChanged: false,
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

    get numberOfConflicts() {
        const {calendars: {currentBooking, newBooking}, timeChanged} = this.state;
        const data = this.isOngoingBooking && timeChanged ? newBooking.data : currentBooking.data;
        return this.getNumberOfOccurrenceByType(data, 'conflicts');
    }

    get numberOfCandidates() {
        const {calendars: {currentBooking, newBooking}, timeChanged} = this.state;
        const data = this.isOngoingBooking && timeChanged ? newBooking.data : currentBooking.data;
        return this.getNumberOfOccurrenceByType(data, 'candidates');
    }

    get numberOfOccurrences() {
        const {calendars: {currentBooking: {data}}} = this.state;
        return this.getNumberOfOccurrenceByType(data, 'bookings');
    }

    get isOngoingBooking() {
        const {booking: {startDt, endDt}} = this.props;
        return moment().isBetween(startDt, endDt, 'day');
    }

    getNumberOfOccurrenceByType = (data, type) => {
        if (!(type in data)) {
            return 0;
        } else if (type === 'conflicts') {
            return Object.values(data.conflicts).filter(conflicts => conflicts.length !== 0).length;
        }
        return Object.values(data[type]).reduce((acc, cur) => acc + (cur.length ? 1 : 0), 0);
    };

    resetCalendarStateOnUpdate = (timeChanged) => {
        const {calendars: {currentBooking, newBooking}} = this.state;
        const newState = {timeChanged, calendars: {currentBooking}};

        if (this.isOngoingBooking && timeChanged) {
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

    updateCalendarsState = (dateRange, newDateRange, candidates, conflicts) => {
        const {timeChanged, calendars: {currentBooking}} = this.state;
        let newCalendars;

        if (this.isOngoingBooking && timeChanged) {
            const {data: {bookings}} = currentBooking;
            const pendingCancelations = _.fromPairs(Object.entries(bookings).map(([day, data]) => {
                if (moment().isAfter(day, 'day')) {
                    return [day, data];
                }
                return [];
            }));

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

        this.setState({calendars: newCalendars});
    };

    updateBookingCalendar = async (dates, timeSlot, recurrence) => {
        const {booking: {room: {id}, dateRange, id: bookingId, startDt, endDt, repetition}} = this.props;
        const {calendars: {currentBooking}} = this.state;
        const {startTime: newStartTime, endTime: newEndTime} = timeSlot;
        const timeChanged = (
            serializeTime(startDt) !== newStartTime ||
            serializeTime(endDt) !== newEndTime ||
            !_.isEqual(getRecurrenceInfo(repetition), recurrence)
        );

        if (this.isOngoingBooking && timeChanged) {
            const today = moment();
            dates.startDate = today.isBefore(dates.startDate) ? serializeDate(dates.startDate) : serializeDate(today);
        }

        this.resetCalendarStateOnUpdate(timeChanged);

        const params = preProcessParameters({timeSlot, recurrence, dates}, ajaxFilterRules);
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
            if (day in currentBooking.data.cancellations || day in currentBooking.data.rejections) {
                return [day, []];
            }
            return [day, allConflicts.filter((c) => !c.reservation || c.reservation.id !== bookingId)];
        }));

        if (_.isEqual(newDateRange, dateRange)) {
            candidates = newDateRange.reduce((accum, day) => {
                if (!(day in currentBooking.data.bookings)) {
                    accum[day] = availabilityData.candidates[day];
                } else {
                    const dayBookings = currentBooking.data.bookings[day];
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

        // Filter out rejections and cancellations from candidates
        const {data: {cancellations, rejections}} = currentBooking;
        candidates = _.pick(candidates, newDateRange.filter(date => !(date in rejections) && !(date in cancellations)));

        this.updateCalendarsState(dateRange, newDateRange, candidates, conflicts);
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
                            {this.isOngoingBooking && (
                                <Message color="blue" size="mini" icon>
                                    <Icon name="play" />
                                    <div styleName="ongoing-booking-info">
                                        <Translate>
                                            This booking has already started.
                                        </Translate>
                                    </div>
                                </Message>
                            )}
                            <BookingEditForm booking={booking}
                                             formProps={fprops}
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
        const {calendars: {currentBooking, newBooking}, timeChanged} = this.state;
        const {booking: {room}} = this.props;
        const legendLabels = [
            {label: Translate.string('Current booking'), color: 'orange', style: 'booking'},
            {label: Translate.string('Cancelled occurrences'), style: 'cancellation'},
            {label: Translate.string('Pending cancelations'), style: 'pending-cancelation'},
            {label: Translate.string('Rejected occurrences'), style: 'rejection'},
            {label: Translate.string('Other bookings'), style: 'other'},
            {label: Translate.string('New booking'), color: 'green', style: 'new-booking'},
            {label: Translate.string('Conflicts with new booking'), color: 'red', style: 'conflict'},
        ];
        const serializeRow = (av) => {
            return (day) => {
                return {
                    availability: {
                        bookings: av.bookings[day] || [],
                        cancellations: av.cancellations[day] || [],
                        rejections: av.rejections[day] || [],
                        other: av.other[day] || [],
                        candidates: (av.candidates[day] || []).map(candidate => ({...candidate, bookable: false})),
                        conflicts: av.conflicts[day] || [],
                        pendingCancelations: av.pendingCancelations[day] || [],
                    },
                    label: serializeDate(day, 'L'),
                    key: day,
                    room,
                };
            };
        };

        const getTimelineRows = (calendar) => {
            const {isFetching, dateRange, data} = calendar;
            return isFetching ? [] : dateRange.map(serializeRow(data));
        };

        return (
            <div styleName="booking-calendar">
                <Header className="legend-header">
                    <span>
                        <Translate>Occurrences</Translate>
                    </span>
                    <Popup trigger={<Icon name="info circle" className="legend-info-icon" />}
                           position="right center"
                           content={<TimelineLegend labels={legendLabels} compact />} />
                    {this.renderNumberOfOccurrences()}
                </Header>
                {this.isOngoingBooking && timeChanged && (
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
                        <DailyTimelineContent rows={getTimelineRows(currentBooking)}
                                              maxHour={24}
                                              renderHeader={this.isOngoingBooking && timeChanged ? () => (
                                                  <Header as="h3" color="orange" styleName="original-booking-header">
                                                      <Translate>Original booking</Translate>
                                                  </Header>
                                              ) : null}
                                              isLoading={currentBooking.isFetching}
                                              fixedHeight={currentBooking.dateRange.length > 0 ? '100%' : null} />
                    </div>
                    {newBooking && (
                        <div styleName="new-booking">
                            <DailyTimelineContent rows={getTimelineRows(newBooking)}
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
    };

    renderNumberOfOccurrences = () => {
        const {timeChanged, calendars: {currentBooking: {data: {bookings}}}} = this.state;
        const today = moment();
        let numNewCandidates = 0;
        let numBookingPastOccurrences = 0;

        if (this.numberOfConflicts) {
            numNewCandidates = this.numberOfCandidates - this.numberOfConflicts;
        } else {
            numNewCandidates = this.numberOfCandidates;
        }

        if (this.isOngoingBooking && timeChanged) {
            numBookingPastOccurrences = Object.entries(bookings).reduce((acc, [day, data]) => {
                if (today.isAfter(day, 'day')) {
                    return acc + data.length;
                }
                return acc;
            }, 0);
        }

        return (
            <div styleName="occurrence-count">
                <Popup trigger={<Label color="blue" size="tiny" content={this.numberOfOccurrences} circular />}
                       position="bottom center"
                       on="hover">
                    <Translate>
                        Number of booking occurrences
                    </Translate>
                </Popup>
                {numNewCandidates > 0 && (
                    <div>
                        {numBookingPastOccurrences > 0 && (
                            <div styleName="old-occurrences-count">
                                <div styleName="arrow">→</div>
                                <Popup trigger={<Label size="tiny" content={numBookingPastOccurrences}
                                                       color="orange"
                                                       circular />}
                                       position="bottom center"
                                       on="hover">
                                    <Translate>
                                        Number of past occurrences that will not be modified
                                    </Translate>
                                </Popup>
                            </div>
                        )}
                        <div className={toClasses({'new-occurrences-count': true, 'single-arrow': numBookingPastOccurrences === 0})}>
                            <div styleName="arrow">→</div>
                            <Popup trigger={<Label size="tiny" content={numNewCandidates}
                                                   color="green"
                                                   circular />}
                                   position="bottom center"
                                   on="hover">
                                <Translate>
                                    Number of new occurrences after changes
                                </Translate>
                            </Popup>
                        </div>
                    </div>
                )}
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
                                booking are unavailable due to conflicts.
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
