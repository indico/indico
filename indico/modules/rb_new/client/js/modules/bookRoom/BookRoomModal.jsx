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
import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import PropTypes from 'prop-types';
import {Button, Checkbox, Form, Grid, Icon, Label, Message, Modal, Radio, Segment, Popup} from 'semantic-ui-react';
import {Form as FinalForm, Field} from 'react-final-form';
import createDecorator from 'final-form-calculate';
import {ReduxFormField, ReduxRadioField, formatters} from 'indico/react/forms';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import PrincipalSearchField from 'indico/react/components/PrincipalSearchField';
import {Overridable} from 'indico/react/util';
import {toMoment} from 'indico/utils/date';
import {selectors as roomsSelectors} from '../../common/rooms';
import recurrenceRenderer from './filters/RecurrenceRenderer';
import RoomBasicDetails from '../../components/RoomBasicDetails';
import {DailyTimelineContent, TimelineLegend} from '../../common/timeline';
import * as actions from './actions';
import {selectors as userSelectors} from '../../common/user';

import './BookRoomModal.module.scss';


function validate({usage, user, reason}) {
    const errors = {};
    if (!usage) {
        errors.usage = Translate.string('Please choose an option!');
    }
    if (usage === 'someone' && !user) {
        errors.user = Translate.string('Please specify a user');
    }
    if (!reason || reason.length < 3) {
        errors.reason = Translate.string('You need to provide a reason');
    }
    return errors;
}

const formDecorator = createDecorator({
    field: 'usage',
    updates: (usage) => {
        if (usage !== 'someone') {
            return {user: null};
        }
        return {};
    }
});

export function TimeInformation({recurrence, dates: {startDate, endDate}, timeSlot}) {
    const {type} = recurrence;
    const mStartDate = toMoment(startDate);
    const mEndDate = endDate ? toMoment(endDate) : null;
    let timeInfo = null;

    if (timeSlot) {
        const {startTime, endTime} = timeSlot;
        const mStartTime = toMoment(startTime, 'HH:mm');
        const mEndTime = endTime ? toMoment(endTime, 'HH:mm') : null;
        timeInfo = (
            <Segment attached="bottom">
                <Icon name="clock" />
                <strong>{mStartTime.format('LT')}</strong>
                {' → '}
                <strong>{mEndTime.format('LT')}</strong>
            </Segment>
        );
    }

    return (
        <div styleName="booking-time-info">
            <Segment attached="top" color="teal">
                <Icon name="calendar outline" />
                {(endDate && startDate !== endDate)
                    ? (
                        <Translate>
                            <Param name="startDate"
                                   wrapper={<strong />}
                                   value={mStartDate.format('L')} /> to <Param name="endDate"
                                                                               wrapper={<strong />}
                                                                               value={mEndDate.format('L')} />
                        </Translate>
                    ) : (
                        <strong>{mStartDate.format('L')}</strong>
                    )
                }
                {(type === 'daily' || type === 'every') && (
                    <Label basic pointing="left">
                        {recurrenceRenderer(recurrence)}
                    </Label>
                )}
            </Segment>
            {timeInfo}
        </div>
    );
}

TimeInformation.propTypes = {
    recurrence: PropTypes.object.isRequired,
    dates: PropTypes.object.isRequired,
    timeSlot: PropTypes.object
};

TimeInformation.defaultProps = {
    timeSlot: null
};


class BookRoomModal extends React.Component {
    static propTypes = {
        room: PropTypes.object,
        isAdmin: PropTypes.bool.isRequired,
        userFullName: PropTypes.string.isRequired,
        bookingData: PropTypes.object.isRequired,
        onClose: PropTypes.func.isRequired,
        availability: PropTypes.object,
        favoriteUsers: PropTypes.array.isRequired,
        timeInformationComponent: PropTypes.func,
        actions: PropTypes.exact({
            createBooking: PropTypes.func.isRequired,
            fetchAvailability: PropTypes.func.isRequired,
            resetAvailability: PropTypes.func.isRequired,
        }).isRequired,
    };

    static defaultProps = {
        room: null,
        availability: null,
        timeInformationComponent: TimeInformation
    };

    state = {
        skipConflicts: false,
        bookingConflictsVisible: false,
        booking: null,
    };

    componentDidMount() {
        const {actions: {fetchAvailability}, room, bookingData} = this.props;
        fetchAvailability(room, bookingData);
    }

    componentWillUnmount() {
        const {actions: {resetAvailability}} = this.props;
        resetAvailability();
    }

    renderPrincipalSearchField = ({input, showCurrentUserPlaceholder, ...fieldProps}) => {
        const {favoriteUsers, userFullName} = this.props;
        if (showCurrentUserPlaceholder) {
            fieldProps.placeholder = userFullName;
        }
        return (
            <ReduxFormField {...fieldProps}
                            input={{...input, value: input.value || null}}
                            favoriteUsers={favoriteUsers}
                            as={PrincipalSearchField} />
        );
    };

    renderBookingState({submitSucceeded, submitError, submitFailed, values}) {
        if (submitSucceeded) {
            const {booking} = this.state;
            const bookingLink = (
                // TODO: add link to view booking details
                // eslint-disable-next-line no-alert
                <a onClick={() => alert(`TODO: View booking ${booking.id}`)} />
            );
            return (
                <Message color={values.isPrebooking ? 'orange' : 'green'}>
                    <Message.Header>
                        {values.isPrebooking ? (
                            <Translate>The room has been pre-booked!</Translate>
                        ) : (
                            <Translate>The room has been booked!</Translate>
                        )}
                    </Message.Header>
                    {values.isPrebooking ? (
                        <Translate>
                            You can consult your pre-booking <Param name="link" wrapper={bookingLink}>here</Param>.
                        </Translate>
                    ) : (
                        <Translate>
                            You can consult your booking <Param name="link" wrapper={bookingLink}>here</Param>.
                        </Translate>
                    )}
                </Message>
            );
        } else if (submitFailed) {
            return (
                <Message color="red">
                    <Message.Header>
                        <Translate>Couldn't book the room</Translate>
                    </Message.Header>
                    {submitError}
                </Message>
            );
        } else {
            return null;
        }
    }

    renderBookingButton(isPrebooking, bookingBlocked, {pristine, hasValidationErrors, form, submitting, values}) {
        return (
            <Button primary={!isPrebooking}
                    color={isPrebooking ? 'orange' : null}
                    disabled={bookingBlocked || pristine || hasValidationErrors}
                    loading={submitting && values.isPrebooking === isPrebooking}
                    type="submit"
                    form="book-room-form"
                    content={(
                        isPrebooking ? (
                            Translate.string('Create Pre-booking')
                        ) : (
                            Translate.string('Create Booking')
                        )
                    )}
                    onClick={() => {
                        form.change('isPrebooking', isPrebooking);
                    }} />
        );
    }

    _getRowSerializer(day) {
        const {room} = this.props;
        return ({bookings, pre_bookings: preBookings, candidates, nonbookable_periods: nonbookablePeriods,
                 unbookable_hours: unbookableHours, blockings, conflicts, pre_conflicts: preConflicts}) => ({
            availability: {
                candidates: candidates[day].map((candidate) => ({...candidate, bookable: false})) || [],
                preBookings: preBookings[day] || [],
                bookings: bookings[day] || [],
                conflicts: conflicts[day] || [],
                preConflicts: preConflicts[day] || [],
                nonbookablePeriods: nonbookablePeriods[day] || [],
                unbookableHours: unbookableHours || [],
                blockings: blockings[day] || []
            },
            label: moment(day).format('L'),
            key: day,
            conflictIndicator: true,
            room
        });
    }

    renderRoomTimeline(availability) {
        const hourSeries = _.range(6, 24, 2);
        const {availability: {dateRange}} = this.props;
        const rows = dateRange.map((day) => this._getRowSerializer(day)(availability));
        return <DailyTimelineContent rows={rows} hourSeries={hourSeries} />;
    }

    renderBookingConstraints(conflicts) {
        const {skipConflicts} = this.state;

        return (
            <>
                <Message color="yellow" attached icon>
                    <Icon name="warning circle" />
                    <Message.Content>
                        <Message.Header>
                            <Translate>Booking conflicts</Translate>
                        </Message.Header>
                        <PluralTranslate count={conflicts.length}>
                            <Singular>
                                Your booking conflicts with another existing one.
                            </Singular>
                            <Plural>
                                <Param name="count" value={conflicts.length} /> occurrences of your booking
                                conflict with existing bookings.
                            </Plural>
                        </PluralTranslate>
                    </Message.Content>
                </Message>
                <Segment attached="bottom">
                    <Checkbox toggle
                              defaultChecked={skipConflicts}
                              label={Translate.string('I understand, please skip any days with conflicting occurrences.')}
                              onChange={(__, {checked}) => {
                                  this.setState({
                                      skipConflicts: checked
                                  });
                              }} />
                </Segment>
            </>
        );
    }

    submitBooking = async (data) => {
        const {actions: {createBooking}} = this.props;
        const rv = await createBooking(data, this.props);
        if (rv.error) {
            return rv.error;
        } else {
            this.setState({booking: rv.data.booking});
        }
    };

    onClose = () => {
        const {onClose} = this.props;
        // reset state when dialog is closed
        this.setState({
            skipConflicts: false
        });
        onClose();
    };

    render() {
        const {
            bookingData: {recurrence, dates, timeSlot},
            room, isAdmin, availability,
            timeInformationComponent: TimeInformationComponent
        } = this.props;
        const {skipConflicts, bookingConflictsVisible} = this.state;

        if (!room) {
            return null;
        }

        const conflictsExist = availability && !!Object.keys(availability.conflicts).length;
        const bookingBlocked = ({submitting, submitSucceeded}) => submitting || submitSucceeded;
        const buttonsBlocked = (fprops) => bookingBlocked(fprops) || (conflictsExist && !skipConflicts);
        const {is_auto_confirm: isDirectlyBookable} = room;
        const link = <a onClick={() => this.setState({bookingConflictsVisible: true})} />;
        const legendLabels = [
            {label: Translate.string('Available'), color: 'green'},
            {label: Translate.string('Booked'), color: 'orange'},
            {label: Translate.string('Pre-Booking'), style: 'pre-booking'},
            {label: Translate.string('Conflict'), color: 'red'},
            {label: Translate.string('Conflict with Pre-Booking'), style: 'pre-booking-conflict'},
            {label: Translate.string('Blocked'), style: 'blocking'},
            {label: Translate.string('Not bookable'), style: 'unbookable'}
        ];
        const renderModalContent = (fprops) => (
            <>
                <Modal.Header>
                    <Translate>Book a Room</Translate>
                </Modal.Header>
                <Modal.Content>
                    <Grid>
                        <Grid.Column width={8}>
                            <RoomBasicDetails room={room} />
                            <Overridable id="TimeInformation">
                                <TimeInformationComponent dates={dates} timeSlot={timeSlot} recurrence={recurrence} />
                            </Overridable>
                            <Message attached="bottom">
                                <Message.Content>
                                    <Translate>
                                        Consult the <Param name="bookings-link" wrapper={link}>timeline view </Param> to
                                        see the other room bookings for the selected period.
                                    </Translate>
                                </Message.Content>
                            </Message>
                        </Grid.Column>
                        <Grid.Column width={8}>
                            <Segment inverted color="blue">
                                <Form inverted id="book-room-form" onSubmit={fprops.handleSubmit}>
                                    <h2><Icon name="user" />Usage</h2>
                                    <Form.Group>
                                        <Field name="usage"
                                               radioValue="myself"
                                               component={ReduxRadioField}
                                               as={Radio}
                                               componentLabel={Translate.string("I'll be using it myself")}
                                               disabled={bookingBlocked(fprops)} />
                                        <Field name="usage"
                                               radioValue="someone"
                                               component={ReduxRadioField}
                                               as={Radio}
                                               componentLabel={Translate.string("I'm booking it for someone else")}
                                               disabled={bookingBlocked(fprops)} />
                                    </Form.Group>
                                    <Field name="user"
                                           component={this.renderPrincipalSearchField}
                                           disabled={bookingBlocked(fprops) || fprops.values.usage !== 'someone'}
                                           showCurrentUserPlaceholder={fprops.values.usage === 'myself'} />
                                    <Field name="reason"
                                           component={ReduxFormField}
                                           as={Form.TextArea}
                                           format={formatters.trim}
                                           formatOnBlur
                                           placeholder={Translate.string('Reason for booking')}
                                           disabled={bookingBlocked(fprops)} />
                                </Form>
                            </Segment>
                            {conflictsExist && this.renderBookingConstraints(Object.values(availability.conflicts))}
                            {this.renderBookingState(fprops)}
                        </Grid.Column>
                    </Grid>
                </Modal.Content>
                <Modal.Actions>
                    {(isDirectlyBookable || isAdmin) && (
                        this.renderBookingButton(false, buttonsBlocked(fprops), fprops)
                    )}
                    {!isDirectlyBookable && this.renderBookingButton(true, buttonsBlocked(fprops), fprops)}
                    <Button type="button" onClick={this.onClose} content={(fprops.submitSucceeded
                        ? Translate.string('Close')
                        : Translate.string("I've changed my mind!"))} />
                    <Modal open={bookingConflictsVisible}
                           onClose={() => this.setState({bookingConflictsVisible: false})}
                           size="large" closeIcon>
                        <Modal.Header className="legend-header">
                            <Translate>Bookings</Translate>
                            <Popup trigger={<Icon name="info circle" className="legend-info-icon" />}
                                   content={<TimelineLegend labels={legendLabels} compact />} />
                        </Modal.Header>
                        <Modal.Content scrolling>
                            {availability && this.renderRoomTimeline(availability)}
                        </Modal.Content>
                    </Modal>
                </Modal.Actions>
            </>
        );

        return (
            <Modal open onClose={this.onClose} size="large" closeIcon>
                <FinalForm onSubmit={this.submitBooking} validate={validate} decorators={[formDecorator]}
                           render={renderModalContent} />
            </Modal>
        );
    }
}

export default connect(
    (state, {roomId}) => ({
        favoriteUsers: userSelectors.getFavoriteUsers(state),
        isAdmin: userSelectors.isUserAdmin(state),
        userFullName: userSelectors.getUserFullName(state),
        availability: state.bookRoom.bookingForm.availability,
        room: roomsSelectors.getRoom(state, {roomId}),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchAvailability: actions.fetchBookingAvailability,
            resetAvailability: actions.resetBookingAvailability,
            createBooking: (data, props) => {
                const {reason, usage, user, isPrebooking} = data;
                const {bookingData: {recurrence, dates, timeSlot}, room} = props;
                return actions.createBooking({
                    reason,
                    usage,
                    user,
                    recurrence,
                    dates,
                    timeSlot,
                    room,
                    isPrebooking
                });
            },
        }, dispatch)
    })
)(BookRoomModal);
