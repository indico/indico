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
import PropTypes from 'prop-types';
import {Form as FinalForm, Field} from 'react-final-form';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {
    Button, Confirm, Form, Grid, Header, Icon, Label, List, Message, Modal, Popup, TextArea
} from 'semantic-ui-react';

import {toMoment, serializeDate} from 'indico/utils/date';
import {Param, Translate} from 'indico/react/i18n';
import {ReduxFormField, formatters, validators as v} from 'indico/react/forms';
import {DailyTimelineContent, TimelineLegend} from '../timeline';
import {getRecurrenceInfo, PopupParam} from '../../util';
import RoomBasicDetails from '../../components/RoomBasicDetails';
import RoomKeyLocation from '../../components/RoomKeyLocation';
import TimeInformation from '../../components/TimeInformation';
import {actions as modalActions} from '../../modals';
import LazyBookingObjectLink from './LazyBookingObjectLink';
import * as bookingsSelectors from './selectors';
import * as bookingsActions from './actions';

import './BookingDetails.module.scss';


class BookingDetails extends React.Component {
    static propTypes = {
        onClose: PropTypes.func,
        editButton: PropTypes.func.isRequired,
        booking: PropTypes.object.isRequired,
        bookingStateChangeInProgress: PropTypes.bool.isRequired,
        actions: PropTypes.exact({
            deleteBooking: PropTypes.func.isRequired,
            changeBookingState: PropTypes.func.isRequired,
            openBookingDetails: PropTypes.func.isRequired,
        }).isRequired,
    };

    static defaultProps = {
        onClose: () => {},
    };

    state = {
        occurrencesVisible: false,
        activeConfirmation: null,
    };

    showOccurrences = () => {
        this.setState({occurrencesVisible: true});
    };

    hideOccurrences = () => {
        this.setState({occurrencesVisible: false});
    };

    renderBookedFor = (bookedForUser) => {
        const {fullName: bookedForName, email: bookedForEmail, phone: bookedForPhone} = bookedForUser;
        return (
            <>
                <Header>
                    <Icon name="user" /><Translate>Booked for</Translate>
                </Header>
                <div>{bookedForName}</div>
                {bookedForPhone && <div><Icon name="phone" />{bookedForPhone}</div>}
                {bookedForEmail && <div><Icon name="mail" />{bookedForEmail}</div>}
            </>
        );
    };

    renderReason = (reason) => (
        <Message info icon styleName="message-icon">
            <Icon name="info" />
            <Message.Content>
                <Message.Header>
                    <Translate>Booking reason</Translate>
                </Message.Header>
                {reason}
            </Message.Content>
        </Message>
    );

    _getRowSerializer = (day) => {
        const {booking: {room}} = this.props;
        return ({bookings, cancellations, rejections, otherBookings}) => ({
            availability: {
                bookings: bookings[day].map((candidate) => ({...candidate, bookable: false})) || [],
                cancellations: cancellations[day] || [],
                rejections: rejections[day] || [],
                other: otherBookings[day] || [],
            },
            label: moment(day).format('L'),
            key: day,
            room
        });
    };

    renderTimeline = (occurrences, dateRange) => {
        const {booking} = this.props;
        const rows = dateRange.map((day) => this._getRowSerializer(day)(occurrences));
        return (
            <DailyTimelineContent rows={rows}
                                  fixedHeight={rows.length > 1 ? '70vh' : null}
                                  booking={booking}
                                  rowActions={{occurrence: true}} />
        );
    };

    renderBookingHistory = (editLogs, createdOn, createdByUser) => {
        if (createdByUser) {
            const {fullName: createdBy} = createdByUser;
            editLogs = [...editLogs, {
                id: 'created',
                timestamp: createdOn,
                info: ['Booking created'],
                userName: createdBy
            }];
        }
        const items = editLogs.map((log) => {
            const {id, timestamp, info, userName} = log;
            const basicInfo = <strong>{info[0]}</strong>;
            const details = (info[1] ? info[1] : null);
            const logDate = serializeDate(toMoment(timestamp), 'L');
            const popupContent = <span styleName="popup-center">{details}</span>;
            const wrapper = (details ? <PopupParam content={popupContent} /> : <span />);
            return (
                <List.Item key={id}>
                    <Translate>
                        <Param name="date" value={logDate} wrapper={<span styleName="log-date" />} />
                        {' - '}
                        <Param name="info" wrapper={wrapper} value={basicInfo} /> by
                        {' '}
                        <Param name="user" value={userName} />
                    </Translate>
                </List.Item>
            );
        });
        return !!items.length && (
            <div styleName="booking-logs">
                <Header><Translate>Booking history</Translate></Header>
                <List divided styleName="log-list">{items}</List>
            </div>
        );
    };

    renderMessageAfterSplitting = (newBookingId) => {
        if (newBookingId === undefined) {
            return null;
        }

        const {actions: {openBookingDetails}} = this.props;
        const link = <a onClick={() => openBookingDetails(newBookingId)} />;
        return (
            <Message color="green">
                <Message.Header>
                    <Translate>
                        The booking has been successfully split.
                    </Translate>
                </Message.Header>
                <Translate>
                    You can consult your new booking <Param name="link" wrapper={link}>here</Param>.
                </Translate>
            </Message>
        );
    };

    renderBookingStatus = () => {
        const {booking: {isPending, isAccepted, isCancelled, isRejected, rejectionReason}} = this.props;
        let color, status, icon, message;

        if (isPending) {
            icon = <Icon name="wait" />;
            color = 'yellow';
            status = Translate.string('Pending Confirmation');
            message = Translate.string('This booking is subject to acceptance by the room owner');
        } else if (isCancelled) {
            icon = <Icon name="cancel" />;
            color = 'grey';
            status = Translate.string('Cancelled');
            message = (
                <>
                    <Translate>
                        The booking was cancelled.
                    </Translate>
                    {!!rejectionReason && (
                        <>
                            <br />
                            <Translate>
                                Reason: <Param name="rejectionReason" value={rejectionReason} wrapper={<strong />} />
                            </Translate>
                        </>
                    )}
                </>
            );
        } else if (isRejected) {
            icon = <Icon name="calendar minus" />;
            color = 'red';
            status = Translate.string('Rejected');
            message = (
                <>
                    <Translate>
                        The booking was rejected.
                    </Translate>
                    {!!rejectionReason && (
                        <>
                            <br />
                            <Translate>
                                Reason: <Param name="rejectionReason" value={rejectionReason} wrapper={<strong />} />
                            </Translate>
                        </>
                    )}
                </>
            );
        } else if (isAccepted) {
            icon = <Icon name="checkmark" />;
            color = 'green';
            status = Translate.string('Accepted');
            message = Translate.string('The booking was accepted');
        }

        const label = (
            <Label color={color}>
                {icon}
                {status}
            </Label>
        );

        return (
            <Popup trigger={label}
                   content={message}
                   position="bottom center" />
        );
    };

    renderDeleteButton = () => {
        const {activeConfirmation} = this.state;
        const {bookingStateChangeInProgress} = this.props;
        return (
            <>
                <Button icon="trash"
                        onClick={() => this.showConfirm('delete')}
                        disabled={bookingStateChangeInProgress}
                        negative
                        circular />
                <Confirm header={Translate.string('Confirm deletion')}
                         content={Translate.string('Are you sure you want to delete this booking?')}
                         confirmButton={<Button content={Translate.string('Delete')} negative />}
                         cancelButton={Translate.string('Cancel')}
                         open={activeConfirmation === 'delete'}
                         onCancel={this.hideConfirm}
                         onConfirm={this.deleteBooking} />
            </>
        );
    };

    deleteBooking = () => {
        const {actions: {deleteBooking}, booking: {id}, onClose} = this.props;
        deleteBooking(id);
        onClose();
        this.hideConfirm();
    };

    hideConfirm = () => {
        this.setState({activeConfirmation: null});
    };

    showConfirm = (type) => {
        this.setState({activeConfirmation: type});
    };

    changeState = (action, data = {}) => {
        const {booking: {id}, actions: {changeBookingState}} = this.props;
        this.setState({actionInProgress: action});
        return changeBookingState(id, action, data).then(() => {
            this.setState({actionInProgress: null});
        });
    };

    renderActionButtons = (canCancel, canReject, showAccept) => {
        const {bookingStateChangeInProgress} = this.props;
        const {actionInProgress, activeConfirmation} = this.state;
        const rejectButton = (
            <Button type="button"
                    icon="remove circle"
                    color="red"
                    size="small"
                    loading={actionInProgress === 'reject' && bookingStateChangeInProgress}
                    disabled={bookingStateChangeInProgress}
                    content={Translate.string('Reject booking')} />
        );

        const renderForm = ({handleSubmit, hasValidationErrors, submitSucceeded, submitting, pristine}) => {
            return (
                <Form styleName="rejection-form" onSubmit={handleSubmit}>
                    <Field name="reason"
                           component={ReduxFormField}
                           as={TextArea}
                           format={formatters.trim}
                           placeholder={Translate.string('Provide the rejection reason')}
                           rows={2}
                           validate={v.required}
                           disabled={submitting}
                           required
                           formatOnBlur />
                    <Button type="submit"
                            disabled={submitting || pristine || hasValidationErrors || submitSucceeded}
                            loading={submitting}
                            floated="right"
                            primary>
                        <Translate>Reject</Translate>
                    </Button>
                </Form>
            );
        };

        return (
            <Modal.Actions>
                {canCancel && (
                    <>
                        <Button type="button"
                                icon="cancel"
                                size="small"
                                onClick={() => this.showConfirm('cancel')}
                                loading={actionInProgress === 'cancel' && bookingStateChangeInProgress}
                                disabled={bookingStateChangeInProgress}
                                content={Translate.string('Cancel booking')} />
                        <Confirm header={Translate.string('Confirm cancellation')}
                                 content={Translate.string('Are you sure you want to cancel this booking? ' +
                                                           'This will cancel all occurrences of this booking.')}
                                 confirmButton={<Button content={Translate.string('Cancel booking')} negative />}
                                 cancelButton={Translate.string('Close')}
                                 open={activeConfirmation === 'cancel'}
                                 onCancel={this.hideConfirm}
                                 onConfirm={() => {
                                     this.changeState('cancel');
                                     this.hideConfirm();
                                 }} />
                    </>
                )}
                {canReject && (
                    <Popup trigger={rejectButton}
                           position="bottom center"
                           on="click">
                        <FinalForm onSubmit={(data) => this.changeState('reject', data)}
                                   render={renderForm} />
                    </Popup>
                )}
                {showAccept && (
                    <Button type="button"
                            icon="check circle"
                            color="green"
                            size="small"
                            onClick={() => this.changeState('approve')}
                            loading={actionInProgress === 'approve' && bookingStateChangeInProgress}
                            disabled={bookingStateChangeInProgress}
                            content={Translate.string('Accept booking')} />
                )}
            </Modal.Actions>
        );
    };

    render() {
        const {occurrencesVisible} = this.state;
        const {
            onClose,
            editButton,
            bookingStateChangeInProgress,
            booking: {
                startDt, endDt, occurrences, dateRange, repetition, room, bookedForUser, bookingReason, editLogs,
                createdDt, createdByUser, isCancelled, isRejected, canDelete, canCancel, canReject, canAccept, canEdit,
                isAccepted, newBookingId, isLinkedToObject, link
            },
        } = this.props;
        const legendLabels = [
            {label: Translate.string('Current'), color: 'orange', style: 'booking'},
            {label: Translate.string('Cancelled'), style: 'cancellation'},
            {label: Translate.string('Rejected'), style: 'rejection'},
            {label: Translate.string('Other bookings'), style: 'other'},
        ];
        const dates = {startDate: startDt, endDate: endDt};
        const times = {startTime: moment(startDt).format('HH:mm'), endTime: moment(endDt).format('HH:mm')};
        const recurrence = getRecurrenceInfo(repetition);
        const showAccept = canAccept && !isAccepted;
        const showActionButtons = (!isCancelled && !isRejected && (canCancel || canReject || showAccept));
        const activeBookings = _.omitBy(occurrences.bookings, (value) => _.isEmpty(value));
        const occurrenceCount = Object.keys(activeBookings).length;
        return (
            <>
                <Modal onClose={onClose} size="large" closeIcon open>
                    <Modal.Header styleName="booking-modal-header">
                        <span styleName="header-text">
                            <Translate>Booking Details</Translate>
                        </span>
                        <span styleName="booking-status">
                            {this.renderBookingStatus()}
                        </span>
                        <span>
                            {canEdit && editButton({disabled: bookingStateChangeInProgress})}
                            {canDelete && this.renderDeleteButton()}
                        </span>
                    </Modal.Header>
                    <Modal.Content>
                        <Grid columns={2}>
                            <Grid.Column>
                                <RoomBasicDetails room={room} />
                                <RoomKeyLocation room={room} />
                                <TimeInformation recurrence={recurrence}
                                                 dates={dates}
                                                 timeSlot={times}
                                                 onClickOccurrences={this.showOccurrences}
                                                 occurrenceCount={occurrenceCount} />
                            </Grid.Column>
                            <Grid.Column>
                                <>
                                    {bookedForUser && this.renderBookedFor(bookedForUser)}
                                    {this.renderReason(bookingReason)}
                                    {isLinkedToObject && (
                                        <LazyBookingObjectLink type={_.camelCase(link.type)} id={link.id} />
                                    )}
                                    {this.renderBookingHistory(editLogs, createdDt, createdByUser)}
                                    {this.renderMessageAfterSplitting(newBookingId)}
                                </>
                            </Grid.Column>
                        </Grid>
                    </Modal.Content>
                    {showActionButtons && this.renderActionButtons(canCancel, canReject, showAccept)}
                </Modal>
                <Modal open={occurrencesVisible}
                       onClose={this.hideOccurrences}
                       size="large"
                       closeIcon>
                    <Modal.Header className="legend-header">
                        <Translate>Occurrences</Translate>
                        <Popup trigger={<Icon name="info circle" className="legend-info-icon" />}
                               content={<TimelineLegend labels={legendLabels} compact />} />
                    </Modal.Header>
                    <Modal.Content>
                        {this.renderTimeline(occurrences, dateRange)}
                    </Modal.Content>
                </Modal>
            </>
        );
    }
}

export default connect(
    (state) => ({
        bookingStateChangeInProgress: bookingsSelectors.isBookingChangeInProgress(state),
    }),
    (dispatch) => ({
        actions: bindActionCreators({
            changeBookingState: bookingsActions.changeBookingState,
            deleteBooking: bookingsActions.deleteBooking,
            openBookingDetails: bookingId => modalActions.openModal('booking-details', bookingId, null, true),
        }, dispatch)
    }),
)(BookingDetails);
