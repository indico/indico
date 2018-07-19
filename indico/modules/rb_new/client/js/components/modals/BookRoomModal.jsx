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

import React from 'react';
import PropTypes from 'prop-types';
import {Button, Checkbox, Form, Grid, Icon, Label, Message, Modal, Radio, Segment} from 'semantic-ui-react';
import {Form as FinalForm, Field} from 'react-final-form';
import createDecorator from 'final-form-calculate';
import {ReduxFormField, ReduxRadioField, formatters} from 'indico/react/forms';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import UserSearchField from 'indico/react/components/UserSearchField';
import recurrenceRenderer from '../filters/RecurrenceRenderer';
import {toMoment} from '../../util';
import {RoomBasicDetails} from '../RoomBasicDetails';
import TimelineContent from '../TimelineContent';

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


export default class BookRoomModal extends React.Component {
    static propTypes = {
        open: PropTypes.bool,
        room: PropTypes.object,
        user: PropTypes.object.isRequired,
        bookingData: PropTypes.object.isRequired,
        onSubmit: PropTypes.func.isRequired,
        onClose: PropTypes.func.isRequired,
        availability: PropTypes.object,
        dateRange: PropTypes.array,
        fetchAvailability: PropTypes.func.isRequired
    };

    static defaultProps = {
        open: false,
        room: null,
        availability: null,
        dateRange: null
    };

    state = {
        skipConflicts: false,
        bookingConflictsVisible: false,
        booking: null,
    };

    componentDidMount() {
        const {availability, fetchAvailability} = this.props;
        if (!availability) {
            fetchAvailability();
        }
    }

    renderUserSearchField({input, ...props}) {
        return (
            <ReduxFormField input={input}
                            as={UserSearchField}
                            {...props}
                            onChange={(user) => {
                                input.onChange(user);
                            }} />
        );
    }

    renderTimeInformation(recurrence, {startDate, endDate}, {startTime, endTime}) {
        const {type} = recurrence;
        const sDate = toMoment(startDate);
        const eDate = endDate ? toMoment(endDate) : null;
        const sTime = toMoment(startTime, 'HH:mm');
        const eTime = endTime ? toMoment(endTime, 'HH:mm') : null;

        return (
            <div styleName="booking-time-info">
                <Segment attached="top" color="teal">
                    <Icon name="calendar outline" />
                    {(endDate && startDate !== endDate)
                        ? (
                            <Translate>
                                <Param name="startTime"
                                       wrapper={<strong />}
                                       value={sDate.format('L')} /> to <Param name="endTime"
                                                                              wrapper={<strong />}
                                                                              value={eDate.format('L')} />
                            </Translate>
                        ) : (
                            <strong>{sDate.format('L')}</strong>
                        )
                    }
                    {(type === 'daily' || type === 'every') && (
                        <Label basic pointing="left">
                            {recurrenceRenderer(recurrence)}
                        </Label>
                    )}
                </Segment>
                <Segment attached="bottom">
                    <Icon name="clock" />
                    <strong>{sTime.format('LT')}</strong>
                    {' '}&rarr;{' '}
                    <strong>{eTime.format('LT')}</strong>
                </Segment>
            </div>
        );
    }

    renderBookingState({submitSucceeded, submitError, submitFailed, values}) {
        if (submitSucceeded) {
            const {booking} = this.state;
            const bookingLink = (
                // TODO: add link to view booking details
                <a style={{cursor: 'pointer'}} onClick={() => alert(`TODO: View booking ${booking.id}`)} />
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
                            You can consult your booking <Param name="link" wrapper={bookingLink}>here</Param>.
                        </Translate>
                    ) : (
                        <Translate>
                            You can consult your pre-booking <Param name="link" wrapper={bookingLink}>here</Param>.
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

    renderRoomTimeline(availability) {
        const hourSeries = _.range(6, 24, 2);
        const {dateRange} = this.props;
        const room = availability.room;
        const rows = dateRange.map((dt) => {
            const av = {
                candidates: availability.candidates[dt].map((candidate) => ({...candidate, bookable: false})) || [],
                preBookings: availability.pre_bookings[dt] || [],
                bookings: availability.bookings[dt] || [],
                conflicts: availability.conflicts[dt] || [],
                preConflicts: availability.pre_conflicts[dt] || []
            };
            return {id: dt, label: dt, conflictIndicator: true, availability: av, room};
        });

        return <TimelineContent rows={rows} hourSeries={hourSeries} />;
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
                              onChange={(_, {checked}) => {
                                  this.setState({
                                      skipConflicts: checked
                                  });
                              }} />
                </Segment>
            </>
        );
    }

    submitBooking = async (data) => {
        const {onSubmit} = this.props;
        const rv = await onSubmit(data, this.props);
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
            open, room, user, availability
        } = this.props;
        const {skipConflicts, bookingConflictsVisible} = this.state;

        if (!room) {
            return null;
        }

        const conflictsExist = availability && !!Object.keys(availability.conflicts).length;
        const bookingBlocked = ({submitting, submitSucceeded}) => submitting || submitSucceeded;
        const buttonsBlocked = (fprops) => bookingBlocked(fprops) || (conflictsExist && !skipConflicts);
        const {is_auto_confirm: isDirectlyBookable} = room;
        const link = <a style={{cursor: 'pointer'}} onClick={() => this.setState({bookingConflictsVisible: true})} />;

        const renderModalContent = (fprops) => (
            <>
                <Modal.Header>
                    <Translate>Book a Room</Translate>
                </Modal.Header>
                <Modal.Content>
                    <Grid>
                        <Grid.Column width={8}>
                            <RoomBasicDetails room={room} />
                            {this.renderTimeInformation(recurrence, dates, timeSlot)}
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
                                           component={this.renderUserSearchField}
                                           disabled={bookingBlocked(fprops) || fprops.values.usage !== 'someone'} />
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
                    {(isDirectlyBookable || user.isAdmin) && (
                        this.renderBookingButton(false, buttonsBlocked(fprops), fprops)
                    )}
                    {!isDirectlyBookable && this.renderBookingButton(true, buttonsBlocked(fprops), fprops)}
                    <Button type="button" onClick={this.onClose} content={(fprops.submitSucceeded
                        ? Translate.string('Close')
                        : Translate.string("I've changed my mind!"))} />
                    <Modal open={bookingConflictsVisible}
                           onClose={() => this.setState({bookingConflictsVisible: false})}
                           size="large" closeIcon>
                        <Modal.Header>
                            <Translate>Bookings</Translate>
                        </Modal.Header>
                        <Modal.Content scrolling>
                            {availability && this.renderRoomTimeline(availability)}
                        </Modal.Content>
                    </Modal>
                </Modal.Actions>
            </>
        );

        return (
            <Modal open={open} onClose={this.onClose} size="large" closeIcon>
                <FinalForm onSubmit={this.submitBooking} validate={validate} decorators={[formDecorator]}
                           render={renderModalContent} />
            </Modal>
        );
    }
}
