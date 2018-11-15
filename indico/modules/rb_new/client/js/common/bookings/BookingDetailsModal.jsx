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
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Form as FinalForm, Field} from 'react-final-form';
import {Button, Confirm, Modal, Form, Icon, Label, Popup, TextArea} from 'semantic-ui-react';
import {Param, Translate} from 'indico/react/i18n';
import {ReduxFormField, formatters, validators} from 'indico/react/forms';
import BookingDetails from './BookingDetails';
import * as bookingsSelectors from './selectors';
import * as bookRoomActions from './actions';

import './BookingDetailsModal.module.scss';


class BookingDetailsModal extends React.Component {
    static propTypes = {
        booking: PropTypes.object.isRequired,
        bookingStateChangeInProgress: PropTypes.bool.isRequired,
        onClose: PropTypes.func,
        actions: PropTypes.exact({
            changeBookingState: PropTypes.func.isRequired,
            deleteBooking: PropTypes.func.isRequired,
        }).isRequired,
    };

    static defaultProps = {
        onClose: () => {},
    };

    state = {
        actionInProgress: null,
        activeConfirmation: null,
        mode: 'view',
    };

    handleCloseModal = () => {
        const {onClose} = this.props;
        onClose();
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
                           validate={validators.required}
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

    changeState = (action, data = {}) => {
        const {booking: {id}, actions: {changeBookingState}} = this.props;
        this.setState({actionInProgress: action});
        return changeBookingState(id, action, data).then(() => {
            this.setState({actionInProgress: null});
        });
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
            message = Translate.string('This booking was cancelled');
        } else if (isRejected) {
            icon = <Icon name="calendar minus" />;
            color = 'red';
            status = Translate.string('Rejected');
            message = (
                <>
                    <Translate>
                        The booking was rejected.
                    </Translate>
                    <br />
                    <Translate>
                        Reason: <Param name="rejectionReason" value={rejectionReason} wrapper={<strong />} />
                    </Translate>
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

    deleteBooking = () => {
        const {actions: {deleteBooking}, booking: {id}} = this.props;
        deleteBooking(id);
        this.handleCloseModal();
        this.hideConfirm();
    };

    hideConfirm = () => {
        this.setState({activeConfirmation: null});
    };

    showConfirm = (type) => {
        this.setState({activeConfirmation: type});
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

    renderEditButton = () => {
        const {bookingStateChangeInProgress} = this.props;
        return (
            <Button icon="pencil"
                    onClick={() => this.setState({mode: 'edit'})}
                    disabled={bookingStateChangeInProgress}
                    circular />
        );
    };

    render() {
        const {booking} = this.props;
        const {canAccept, canCancel, canDelete, canModify, canReject, isCancelled, isRejected, isAccepted} = booking;
        const {mode} = this.state;
        const showAccept = canAccept && !isAccepted;
        const showActionButtons = (!isCancelled && !isRejected && (canCancel || canReject || showAccept));
        const isBeingEdited = mode === 'edit';

        return (
            <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                <Modal.Header styleName="booking-modal-header">
                    <span styleName="header-text">
                        <Translate>Booking Details</Translate>
                    </span>
                    <span styleName="booking-status">
                        {this.renderBookingStatus()}
                    </span>
                    <span>
                        {canModify && this.renderEditButton()}
                        {canDelete && this.renderDeleteButton()}
                    </span>
                </Modal.Header>
                <Modal.Content>
                    {isBeingEdited ? (
                        <></>
                    ) : (
                        <BookingDetails booking={booking} />
                    )}
                </Modal.Content>
                {showActionButtons && this.renderActionButtons(canCancel, canReject, showAccept)}
            </Modal>
        );
    }
}

export default connect(
    (state, {bookingId}) => ({
        booking: bookingsSelectors.getDetailsWithRoom(state, {bookingId}),
        bookingStateChangeInProgress: bookingsSelectors.isBookingChangeInProgress(state),
    }),
    (dispatch) => ({
        actions: bindActionCreators({
            changeBookingState: bookRoomActions.changeBookingState,
            deleteBooking: bookRoomActions.deleteBooking,
        }, dispatch),
    }),
)(BookingDetailsModal);
