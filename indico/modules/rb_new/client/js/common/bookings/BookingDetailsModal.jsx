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

import moment from 'moment';
import React from 'react';
import PropTypes from 'prop-types';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Form as FinalForm, Field} from 'react-final-form';
import {Button, Modal, Message, Form, Grid, Header, Icon, Label, Popup, List} from 'semantic-ui-react';
import {Param, Translate} from 'indico/react/i18n';
import {toMoment, serializeDate} from 'indico/utils/date';
import {ReduxFormField, formatters} from 'indico/react/forms';
import TimeInformation from '../../components/TimeInformation';
import RoomBasicDetails from '../../components/RoomBasicDetails';
import RoomKeyLocation from '../../components/RoomKeyLocation';
import * as bookingsSelectors from './selectors';
import * as bookRoomActions from './actions';
import {DailyTimelineContent, TimelineLegend} from '../timeline';
import {PopupParam} from '../../util';

import './BookingDetailsModal.module.scss';


class BookingDetailsModal extends React.Component {
    static propTypes = {
        booking: PropTypes.object.isRequired,
        bookingStateChangeInProgress: PropTypes.bool.isRequired,
        onClose: PropTypes.func,
        actions: PropTypes.exact({
            changeBookingStatus: PropTypes.func.isRequired,
        }).isRequired,
    };

    static defaultProps = {
        onClose: () => {}
    };

    state = {
        occurrencesVisible: false,
        actionInProgress: null,
    };

    handleCloseModal = () => {
        const {onClose} = this.props;
        onClose();
    };

    getRecurrence = (repetition) => {
        const repeatFrequency = repetition[0];
        const repeatInterval = repetition[1];
        let type = 'single';
        let number = null;
        let interval = null;
        if (repeatFrequency === 1) {
            type = 'daily';
        } else if (repeatFrequency === 2) {
            type = 'every';
            interval = 'week';
            number = repeatInterval;
        } else if (repeatFrequency === 3) {
            type = 'every';
            interval = 'month';
            number = repeatInterval;
        }
        return ({type, number, interval});
    };

    _getRowSerializer(day) {
        const {booking: {room}} = this.props;
        return (occurrences) => ({
            availability: {
                bookings: occurrences[day].map((candidate) => ({...candidate, bookable: false})) || [],
            },
            label: moment(day).format('L'),
            key: day,
            room
        });
    }

    showOccurrences = () => {
        this.setState({occurrencesVisible: true});
    };

    hideOccurrences = () => {
        this.setState({occurrencesVisible: false});
    };

    renderTimeline = (occurrences, dateRange) => {
        const rows = dateRange.map((day) => this._getRowSerializer(day)(occurrences));
        return (
            <DailyTimelineContent rows={rows}
                                  fixedHeight={rows.length > 1 ? '70vh' : null} />
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

    renderBookedFor = (bookedForUser) => {
        const {fullName: bookedForName, email: bookedForEmail, phone: bookedForPhone} = bookedForUser;
        return (
            <>
                <Header><Icon name="user" /><Translate>Booked for</Translate></Header>
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

    renderActionButtons = (canCancel, canReject, showAccept) => {
        const {bookingStateChangeInProgress} = this.props;
        const {actionInProgress} = this.state;
        const rejectButton = (
            <Button type="button"
                    icon="remove circle"
                    color="red"
                    size="small"
                    loading={actionInProgress === 'reject' && bookingStateChangeInProgress}
                    disabled={actionInProgress === 'approve' && bookingStateChangeInProgress}
                    content={<Translate>Reject booking</Translate>} />
        );

        const validate = ({reason}) => {
            const errors = {};
            if (!reason) {
                errors.reason = Translate.string('Rejection reason is required');
            }
            return errors;
        };

        const renderForm = ({handleSubmit, hasValidationErrors, submitSucceeded, submitting}) => {
            return (
                <Form styleName="rejection-form" onSubmit={handleSubmit}>
                    <Field name="reason"
                           component={ReduxFormField}
                           as={Form.TextArea}
                           format={formatters.trim}
                           placeholder={Translate.string('Provide the rejection reason')}
                           disabled={submitting}
                           rows={2}
                           autoFocus
                           formatOnBlur />
                    <Button type="submit"
                            disabled={hasValidationErrors || submitSucceeded}
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
                    <Button type="button"
                            icon="remove circle"
                            size="small"
                            content={<Translate>Cancel booking</Translate>}
                            required />
                )}
                {canReject && (
                    <Popup trigger={rejectButton}
                           position="right center"
                           on="click">
                        <FinalForm onSubmit={(data) => this.changeState('reject', data)}
                                   validate={validate}
                                   render={renderForm}
                                   initialValues={{reason: ''}} />
                    </Popup>
                )}
                {showAccept && (
                    <Button type="button"
                            icon="check circle"
                            color="green"
                            size="small"
                            onClick={() => this.changeState('approve')}
                            loading={actionInProgress === 'approve' && bookingStateChangeInProgress}
                            disabled={actionInProgress === 'reject' && bookingStateChangeInProgress}
                            content={<Translate>Accept booking</Translate>} />
                )}
            </Modal.Actions>
        );
    };

    changeState = (action, data = {}) => {
        const {booking: {id}, actions: {changeBookingStatus}} = this.props;
        this.setState({actionInProgress: action}, () => {
            changeBookingStatus(id, action, data).then(() => {
                this.setState({actionInProgress: null});
            });
        });
    };

    renderBookingStatus = ({isPending, isAccepted, isCancelled, isRejected, rejectionReason}) => {
        let color, status, icon, message;

        if (isPending) {
            icon = <Icon name="wait" />;
            color = 'yellow';
            status = Translate.string('Pending Confirmation');
            message = Translate.string('The booking is subject to acceptance by the room owner');
        } else if (isCancelled) {
            icon = <Icon name="cancel" />;
            color = 'grey';
            status = Translate.string('Cancelled');
            message = Translate.string('The booking was cancelled');
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

    render() {
        const {
            booking: {
                room, bookedForUser, startDt, endDt, repetition, createdByUser, createdDt, bookingReason,
                occurrences, dateRange, editLogs, canAccept, canCancel, canDelete, canModify, canReject, isCancelled,
                isRejected, isAccepted
            }
        } = this.props;
        const {occurrencesVisible} = this.state;
        const dates = {startDate: startDt, endDate: endDt};
        const times = {startTime: moment(startDt).format('HH:mm'), endTime: moment(endDt).format('HH:mm')};
        const recurrence = this.getRecurrence(repetition);
        const legendLabels = [
            {label: Translate.string('Occurrence'), color: 'orange'},
        ];
        const showAccept = canAccept && !isAccepted;
        const showActionButtons = (!isCancelled && !isRejected && (canCancel || canReject || showAccept));
        return (
            <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                <Modal.Header styleName="booking-modal-header">
                    <span styleName="header-text">
                        <Translate>Booking Details</Translate>
                    </span>
                    <span styleName="booking-status">
                        {/* eslint-disable-next-line react/destructuring-assignment */}
                        {this.renderBookingStatus(this.props.booking)}
                    </span>
                    <span>
                        {canModify && <Button icon="pencil" circular />}
                        {canDelete && <Button icon="trash" circular />}
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
                                             occurrenceCount={dateRange.length} />
                        </Grid.Column>
                        <Grid.Column>
                            {bookedForUser && this.renderBookedFor(bookedForUser)}
                            {this.renderReason(bookingReason)}
                            {this.renderBookingHistory(editLogs, createdDt, createdByUser)}
                        </Grid.Column>
                    </Grid>
                </Modal.Content>
                {showActionButtons && this.renderActionButtons(canCancel, canReject, showAccept)}
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
            changeBookingStatus: bookRoomActions.changeBookingStatus,
        }, dispatch),
    }),
)(BookingDetailsModal);
