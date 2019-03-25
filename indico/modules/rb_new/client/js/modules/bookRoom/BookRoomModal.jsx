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
import {Button, Checkbox, Form, Grid, Icon, Message, Modal, Radio, Segment} from 'semantic-ui-react';
import {Form as FinalForm, Field} from 'react-final-form';
import createDecorator from 'final-form-calculate';
import {ReduxCheckboxField, ReduxDropdownField, ReduxFormField, ReduxRadioField, formatters} from 'indico/react/forms';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import PrincipalSearchField from 'indico/react/components/PrincipalSearchField';
import {Overridable, IndicoPropTypes} from 'indico/react/util';
import {createDT, isBookingStartDTValid} from 'indico/utils/date';
import TimeInformation from '../../components/TimeInformation';
import {selectors as roomsSelectors} from '../../common/rooms';
import {selectors as linkingSelectors, linkDataShape} from '../../common/linking';
import RoomBasicDetails from '../../components/RoomBasicDetails';
import * as actions from './actions';
import {actions as modalActions} from '../../modals';
import {selectors as userSelectors} from '../../common/user';
import * as bookRoomSelectors from './selectors';
import {BookingObjectLink} from '../../common/bookings';
import SingleRoomTimelineModal from '../../common/timeline/SingleRoomTimelineModal';

import './BookRoomModal.module.scss';


function validate({usage, user, reason}, reasonRequired) {
    const errors = {};
    if (!usage) {
        errors.usage = Translate.string('Please choose an option!');
    }
    if (usage === 'someone' && !user) {
        errors.user = Translate.string('Please specify a user');
    }
    if (reasonRequired && !reason) {
        errors.reason = Translate.string('You need to provide a reason');
    }
    if (reason && reason.length < 3) {
        errors.reason = Translate.string('Reason must be at least 3 characters');
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

class BookRoomModal extends React.Component {
    static propTypes = {
        room: PropTypes.object,
        userFullName: PropTypes.string.isRequired,
        bookingData: PropTypes.object.isRequired,
        onClose: PropTypes.func.isRequired,
        availability: PropTypes.object,
        favoriteUsers: PropTypes.array.isRequired,
        timeInformationComponent: PropTypes.func,
        relatedEvents: PropTypes.array.isRequired,
        link: linkDataShape,
        isAdminOverrideEnabled: PropTypes.bool.isRequired,
        actions: PropTypes.exact({
            createBooking: PropTypes.func.isRequired,
            fetchAvailability: PropTypes.func.isRequired,
            resetAvailability: PropTypes.func.isRequired,
            openBookingDetails: PropTypes.func.isRequired,
            fetchRelatedEvents: PropTypes.func.isRequired,
            resetRelatedEvents: PropTypes.func.isRequired
        }).isRequired,
        defaultTitles: PropTypes.shape({
            booking: IndicoPropTypes.i18n,
            preBooking: IndicoPropTypes.i18n
        }),
        reasonRequired: PropTypes.bool,
    };

    static defaultProps = {
        room: null,
        availability: null,
        timeInformationComponent: TimeInformation,
        link: null,
        defaultTitles: {
            booking: <Translate>Create Booking</Translate>,
            preBooking: <Translate>Create Pre-booking</Translate>
        },
        reasonRequired: true,
    };

    state = {
        skipConflicts: false,
        bookingConflictsVisible: false,
        booking: null,
        selectedEvent: null,
    };

    componentDidMount() {
        const {
            actions: {fetchAvailability, fetchRelatedEvents},
            room,
            link,
            bookingData: {isPrebooking, ...data}
        } = this.props;
        fetchAvailability(room, data);
        if (!link) {
            fetchRelatedEvents(room, data);
        }
    }

    componentWillUnmount() {
        const {actions: {resetAvailability, resetRelatedEvents}} = this.props;
        resetAvailability();
        resetRelatedEvents();
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
        const {actions: {openBookingDetails}} = this.props;
        if (submitSucceeded) {
            const {booking} = this.state;
            const bookingLink = (
                <a onClick={() => openBookingDetails(booking.id)} />
            );
            return (
                <Message color={values.isPrebooking ? 'orange' : 'green'}>
                    <Message.Header>
                        {values.isPrebooking ? (
                            <Translate>The space has been successfully pre-booked!</Translate>
                        ) : (
                            <Translate>The space has been successfully booked!</Translate>
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
                    content={isPrebooking ? Translate.string('Create Pre-booking') : Translate.string('Create Booking')}
                    onClick={() => {
                        form.change('isPrebooking', isPrebooking);
                    }} />
        );
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
        const {actions: {createBooking}, link} = this.props;
        if (data.event) {
            // linking an event based on a matching event
            data.linkType = 'event';
            data.linkId = data.event;
            data.linkBack = true;
        } else if (link) {
            // linking an event through linking mode
            data.linkType = _.snakeCase(link.type);
            data.linkId = link.id;
        }
        const rv = await createBooking(data, this.props);
        if (rv.error) {
            return rv.error;
        } else {
            this.setState({booking: rv.data.booking});
        }
    };

    onClose = () => {
        const {onClose} = this.props;
        const {booking} = this.state;
        // reset state when dialog is closed
        this.setState({
            skipConflicts: false
        });
        onClose(booking !== null);
    };

    showConflicts = () => {
        this.setState({bookingConflictsVisible: true});
    };

    hideConflicts = () => {
        this.setState({bookingConflictsVisible: false});
    };

    get hasLinkConflict() {
        const {link, room} = this.props;
        if (!link) {
            return false;
        } else if (link.ownRoomId !== null) {
            // conflict if object is linked to another room
            return link.ownRoomId !== room.id;
        } else {
            // conflict if object has a custom room set
            return link.ownRoomName !== null;
        }
    }

    get alreadyLinked() {
        const {link, room} = this.props;
        return link !== null && link.ownRoomId === room.id;
    }

    renderPrebookingMessage() {
        const wrapper = <strong styleName="pre-booking-color" />;
        return (
            <Message icon>
                <Icon name="warning circle" />
                <Message.Content>
                    <Message.Header>
                        <Translate>
                            You are creating a <Param name="highlight" wrapper={wrapper}>Pre-Booking</Param>
                        </Translate>
                    </Message.Header>
                    <Translate>
                        A Pre-Booking has to be approved by the room managers before you
                        can use the space in question.
                    </Translate>
                </Message.Content>
            </Message>
        );
    }

    getEventOption = (event) => {
        const start = moment(event.startDt).format('L LT');
        const sameDate = moment(event.startDt).isSame(event.endDt, 'date');
        const endTime = moment(event.endDt).format('LT');
        const end = sameDate ? `${endTime}` : `${moment(event.endDt).format('L')} ${endTime}`;
        return {
            text: event.title,
            description: `${start} - ${end}`,
            value: event.id
        };
    };

    renderEventLink = (link) => {
        if (link) {
            return (
                <span styleName="link-active">
                    {/* eslint-disable-next-line react/jsx-no-target-blank */}
                    <a href={link} target="_blank">
                        <Icon name="external" link />
                    </a>
                </span>
            );
        } else {
            return (
                <span styleName="link-inactive">
                    <Icon name="external" />
                </span>
            );
        }
    };

    renderEventField = (options, links, disabled, mutators) => {
        if (options.length > 1) {
            const {selectedEvent} = this.state;
            return (
                <div styleName="event-dropdown">
                    <Field name="event"
                           component={ReduxDropdownField}
                           options={options}
                           placeholder={Translate.string('Choose an event')}
                           disabled={disabled}
                           selection
                           clearable
                           onChange={(value) => {
                               this.setState({
                                   selectedEvent: value
                               });
                           }} />
                    {this.renderEventLink(links[selectedEvent])}
                </div>
            );
        } else {
            const [event] = options;
            return (
                <div styleName="event-checkbox">
                    <span><strong>{event.text}</strong></span>
                    <span styleName="description">{event.description}</span>
                    {this.renderEventLink(links[event.value])}
                    <Checkbox toggle
                              styleName="checkbox"
                              onChange={(__, {checked}) => {
                                  mutators.setEvent(checked ? event.value : undefined);
                              }} />
                </div>
            );
        }
    };

    renderRelatedEventsDropdown = (disabled, mutators) => {
        const {relatedEvents} = this.props;

        if (!relatedEvents.length) {
            return;
        }

        const options = relatedEvents.map(this.getEventOption);
        const links = _.fromPairs(relatedEvents.map(event => [event.id, event.url]));

        return (
            <Segment>
                <h3><Icon name="chain" />{Translate.string('Event')}</h3>
                <div styleName="events-segment-description">
                    <PluralTranslate count={relatedEvents.length}>
                        <Singular>
                            You have an event taking place during the selected time.
                            If you are booking the room for this event, please select it below.
                            The room of the selected event will automatically be updated.
                        </Singular>
                        <Plural>
                            You have events taking place during the selected time.
                            If you are booking this room for one of your events, please select it below.
                            The room of the selected event will automatically be updated.
                        </Plural>
                    </PluralTranslate>
                </div>
                {this.renderEventField(options, links, disabled, mutators)}
            </Segment>
        );
    };

    renderLink(link, disabled) {
        const {room} = this.props;
        const assignMessages = {
            event: Translate.string('Assign the room {room} to this event', {room: room.name}),
            contribution: Translate.string('Assign the room {room} to this contribution', {room: room.name}),
            sessionBlock: Translate.string('Assign the room {room} to this session block', {room: room.name}),
        };
        const replaceMessages = {
            event: (
                <Translate>
                    Assign the room <Param name="room" wrapper={<em />} value={room.name} /> to this event
                    (instead of <Param name="oldRoom" wrapper={<em />} value={link.ownRoomName} />)
                </Translate>
            ),
            contribution: (
                <Translate>
                    Assign the room <Param name="room" wrapper={<em />} value={room.name} /> to this contribution
                    (instead of <Param name="oldRoom" wrapper={<em />} value={link.ownRoomName} />)
                </Translate>
            ),
            sessionBlock: (
                <Translate>
                    Assign the room <Param name="room" wrapper={<em />} value={room.name} /> to this session block
                    (instead of <Param name="oldRoom" wrapper={<em />} value={link.ownRoomName} />)
                </Translate>
            ),
        };
        const label = this.hasLinkConflict ? {children: replaceMessages[link.type]} : assignMessages[link.type];
        return (
            <>
                <BookingObjectLink link={link} pending>
                    {!this.alreadyLinked && (
                        <Field name="linkBack" component={ReduxCheckboxField} disabled={disabled} toggle
                               componentLabel={label} />
                    )}
                </BookingObjectLink>
            </>
        );
    }

    render() {
        const {
            bookingData: {recurrence, dates, timeSlot, isPrebooking},
            room, availability,
            timeInformationComponent: TimeInformationComponent,
            defaultTitles,
            link,
            reasonRequired,
            isAdminOverrideEnabled,
        } = this.props;
        const {skipConflicts, bookingConflictsVisible} = this.state;
        if (!room) {
            return null;
        }
        const linkBack = !!link && !this.hasLinkConflict;
        const occurrenceCount = availability && availability.dateRange.length;
        const conflictsExist = availability && !!Object.keys(availability.conflicts).length;
        const bookingBlocked = ({submitSucceeded}) => submitSucceeded;
        const isStartDtValid = isBookingStartDTValid(
            createDT(dates.startDate, timeSlot.startTime),
            isAdminOverrideEnabled
        );
        const buttonsBlocked = (fprops) => (
            !isStartDtValid ||
            bookingBlocked(fprops) ||
            (conflictsExist && !skipConflicts)
        );
        const legendLabels = [
            {label: Translate.string('Available'), style: 'available'},
            {label: Translate.string('Booked'), style: 'booking'},
            {label: Translate.string('Pre-Booked'), style: 'pre-booking'},
            {label: Translate.string('Invalid occurrence'), style: 'conflicting-candidate'},
            {label: Translate.string('Conflict'), style: 'conflict'},
            {label: Translate.string('Conflict with Pre-Booking'), style: 'pre-booking-conflict'},
            {label: Translate.string('Blocked'), style: 'blocking'},
            {label: Translate.string('Not bookable'), style: 'unbookable'}
        ];
        const renderModalContent = (fprops) => (
            <>
                <Modal.Header>
                    {isPrebooking ? defaultTitles.preBooking : defaultTitles.booking }
                </Modal.Header>
                <Modal.Content>
                    <Grid>
                        <Grid.Column width={8}>
                            <RoomBasicDetails room={room} />
                            <TimeInformationComponent dates={dates}
                                                      timeSlot={timeSlot}
                                                      recurrence={recurrence}
                                                      onClickOccurrences={this.showConflicts}
                                                      occurrenceCount={occurrenceCount} />
                        </Grid.Column>
                        <Grid.Column width={8}>
                            {isPrebooking && this.renderPrebookingMessage()}
                            {link && this.renderLink(link, bookingBlocked(fprops))}
                            <Form id="book-room-form" onSubmit={fprops.handleSubmit}>
                                <Segment inverted color="blue">
                                    <h3>
                                        <Icon name="user" />
                                        <Translate>Usage</Translate>
                                    </h3>
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
                                           render={this.renderPrincipalSearchField}
                                           disabled={bookingBlocked(fprops) || fprops.values.usage !== 'someone'}
                                           required={fprops.values.usage === 'someone'}
                                           showCurrentUserPlaceholder={fprops.values.usage === 'myself'} />
                                    <Field name="reason"
                                           component={ReduxFormField}
                                           as={Form.TextArea}
                                           format={formatters.trim}
                                           formatOnBlur
                                           placeholder={Translate.string('Reason for booking')}
                                           disabled={bookingBlocked(fprops)}
                                           required={reasonRequired} />
                                </Segment>
                                {!link && !fprops.submitSucceeded && (
                                    this.renderRelatedEventsDropdown(bookingBlocked(fprops), fprops.form.mutators)
                                )}
                            </Form>
                            {conflictsExist && this.renderBookingConstraints(Object.values(availability.conflicts))}
                            {this.renderBookingState(fprops)}
                            {!isStartDtValid && (
                                <Message color="red">
                                    <Icon name="dont" />
                                    <Translate>
                                        Bookings in the past are not allowed.
                                    </Translate>
                                </Message>
                            )}
                        </Grid.Column>
                    </Grid>
                </Modal.Content>
                <Modal.Actions>
                    {this.renderBookingButton(isPrebooking, buttonsBlocked(fprops), fprops)}
                    <Button type="button" onClick={this.onClose} content={(fprops.submitSucceeded
                        ? Translate.string('Close')
                        : Translate.string("I've changed my mind!"))} />
                    <SingleRoomTimelineModal open={bookingConflictsVisible}
                                             onClose={this.hideConflicts}
                                             room={room}
                                             title={<Translate>Bookings</Translate>}
                                             legendLabels={legendLabels} />
                </Modal.Actions>
            </>
        );

        return (
            <Modal open onClose={this.onClose} size="large" closeIcon>
                <FinalForm onSubmit={this.submitBooking} validate={(values) => validate(values, reasonRequired)}
                           decorators={[formDecorator]} render={renderModalContent}
                           initialValues={{user: null, linkBack}}
                           mutators={{setEvent: ([event], state, {changeValue}) => {
                               changeValue(state, 'event', () => event);
                           }}} />
            </Modal>
        );
    }
}

export default connect(
    (state, {roomId}) => ({
        favoriteUsers: userSelectors.getFavoriteUsers(state),
        userFullName: userSelectors.getUserFullName(state),
        availability: bookRoomSelectors.getBookingFormAvailability(state),
        relatedEvents: bookRoomSelectors.getBookingFormRelatedEvents(state),
        room: roomsSelectors.getRoom(state, {roomId}),
        link: linkingSelectors.getLinkObject(state),
        isAdminOverrideEnabled: userSelectors.isUserAdminOverrideEnabled(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchAvailability: actions.fetchBookingAvailability,
            resetAvailability: actions.resetBookingAvailability,
            fetchRelatedEvents: actions.fetchRelatedEvents,
            resetRelatedEvents: actions.resetRelatedEvents,
            createBooking: (data, props) => {
                const {reason, usage, user, isPrebooking, linkType, linkId, linkBack} = data;
                const {bookingData: {recurrence, dates, timeSlot}, room, isAdminOverrideEnabled} = props;
                return actions.createBooking({
                    reason,
                    usage,
                    user,
                    recurrence,
                    dates,
                    timeSlot,
                    room,
                    linkType,
                    linkId,
                    linkBack,
                    isPrebooking,
                }, isAdminOverrideEnabled);
            },
            openBookingDetails: bookingId => modalActions.openModal('booking-details', bookingId, null, true)
        }, dispatch)
    })
)(Overridable.component('BookRoomModal', BookRoomModal));
