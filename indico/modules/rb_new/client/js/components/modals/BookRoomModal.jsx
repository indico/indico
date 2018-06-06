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
import {Button, Form, Grid, Icon, Label, Message, Modal, Segment} from 'semantic-ui-react';
import {reduxForm, Field} from 'redux-form';
import {ReduxFormField, ReduxRadioField} from 'indico/react/forms';
import {Translate, Param} from 'indico/react/i18n';
import UserSearchField from 'indico/react/components/UserSearchField';
import recurrenceRenderer from '../filters/RecurrenceRenderer';
import {toMoment} from '../../util';
import {RoomBasicDetails} from '../RoomBasicDetails';

import './BookRoomModal.module.scss';


const normalizeReason = (text) => text.trim();

function validate({usage, user, reason}) {
    const errors = {};
    if (!usage) {
        errors.usage = Translate.string('Please choose an option!');
    }
    if (usage === 'someone' && !user) {
        errors.user = Translate.string('Please specify a user');
    }
    if (!reason) {
        errors.reason = Translate.string('You need to provide a reason');
    }
    return errors;
}


class BookRoomModal extends React.Component {
    static propTypes = {
        open: PropTypes.bool,
        room: PropTypes.object,
        user: PropTypes.object.isRequired,
        handleSubmit: PropTypes.func.isRequired,
        bookingData: PropTypes.object.isRequired,
        bookingState: PropTypes.object,
        onSubmit: PropTypes.func.isRequired,
        onClose: PropTypes.func.isRequired,
        pristine: PropTypes.bool.isRequired,
        invalid: PropTypes.bool.isRequired
    };

    static defaultProps = {
        open: false,
        room: null,
        bookingState: {}
    };

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

    renderBookingState({success, message, isPrebooking}) {
        if (success) {
            return (
                <Message color={isPrebooking ? 'orange' : 'green'}>
                    <Message.Header>
                        {isPrebooking ? (
                            <Translate>The room has been pre-booked!</Translate>
                        ) : (
                            <Translate>The room has been booked!</Translate>
                        )}
                    </Message.Header>
                    <Translate>You can consult your (pre-)booking <Param name="link" wrapper={<a />}>here</Param>.</Translate>
                </Message>
            );
        } else if (success === false) {
            return (
                <Message color="red">
                    <Message.Header>
                        <Translate>Couldn't book the room</Translate>
                    </Message.Header>
                    {message}
                </Message>
            );
        } else {
            return null;
        }
    }

    renderBookingButton(isPrebooking, bookingBlocked) {
        const {pristine, invalid, bookingState, handleSubmit} = this.props;
        return (
            <Button primary={!isPrebooking}
                    color={isPrebooking ? 'orange' : null}
                    disabled={bookingBlocked || pristine || invalid}
                    loading={bookingState.ongoing}
                    type="submit"
                    content={(
                        isPrebooking ? (
                            Translate.string('Create Pre-booking')
                        ) : (
                            Translate.string('Create Booking')
                        )
                    )}
                    onClick={handleSubmit(this.submitFormFactory(isPrebooking))} />
        );
    }

    submitFormFactory = (isPrebooking) => (data, ...args) => {
        const {onSubmit} = this.props;
        onSubmit({...data, isPrebooking}, ...args);
    };

    render() {
        const {bookingData: {recurrence, dates, timeSlot}, open, room, bookingState,
               onClose, user} = this.props;
        if (!room) {
            return null;
        }

        const bookingBlocked = bookingState.success || bookingState.ongoing;
        const {is_auto_confirm: isDirectlyBookable} = room;

        return (
            <Modal open={open} onClose={onClose} closeIcon>
                <Modal.Header>
                    <Translate>Book a Room</Translate>
                </Modal.Header>
                <Modal.Content>
                    <Grid>
                        <Grid.Column width={8}>
                            <RoomBasicDetails room={room} />
                            {this.renderTimeInformation(recurrence, dates, timeSlot)}
                        </Grid.Column>
                        <Grid.Column width={8}>
                            <Segment inverted color="blue">
                                <Form inverted>
                                    <h2><Icon name="user" />Usage</h2>
                                    <Form.Group>
                                        <Field name="usage"
                                               radioValue="myself"
                                               component={ReduxRadioField}
                                               as={Form.Radio}
                                               label={Translate.string("I'll be using it myself")}
                                               disabled={bookingBlocked} />
                                        <Field name="usage"
                                               radioValue="someone"
                                               component={ReduxRadioField}
                                               as={Form.Radio}
                                               label={Translate.string("I'm booking it for someone else")}
                                               disabled={bookingBlocked} />
                                    </Form.Group>
                                    <Field name="user"
                                           component={this.renderUserSearchField}
                                           disabled={bookingBlocked} />
                                    <Field name="reason"
                                           normalize={normalizeReason}
                                           component={ReduxFormField}
                                           as={Form.TextArea}
                                           placeholder={Translate.string('Reason for booking')}
                                           disabled={bookingBlocked} />
                                </Form>
                            </Segment>
                            {this.renderBookingState(bookingState)}
                        </Grid.Column>
                    </Grid>
                </Modal.Content>
                <Modal.Actions>
                    {(isDirectlyBookable || user.isAdmin) &&
                     this.renderBookingButton(false, bookingBlocked)}
                    {!isDirectlyBookable &&
                     this.renderBookingButton(true, bookingBlocked)}
                    <Button content={(bookingState.success
                        ? Translate.string('Close')
                        : Translate.string("I've changed my mind!"))}
                            onClick={onClose} />

                </Modal.Actions>
            </Modal>
        );
    }
}

export default reduxForm({
    form: 'roomModal',
    validate
})(BookRoomModal);
