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
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import {Button, Modal, Message, Grid, Header, Icon, Label, Popup, List} from 'semantic-ui-react';
import {Param, Translate} from 'indico/react/i18n';
import {toMoment, serializeDate} from 'indico/utils/date';
import TimeInformation from '../../components/TimeInformation';
import RoomBasicDetails from '../../components/RoomBasicDetails';
import RoomKeyLocation from '../../components/RoomKeyLocation';
import * as bookingsSelectors from './selectors';
import {DailyTimelineContent, TimelineLegend} from '../timeline';
import {PopupParam} from '../../util';

import './BookingDetailsModal.module.scss';


class BookingDetailsModal extends React.Component {
    static propTypes = {
        booking: PropTypes.object.isRequired,
        onClose: PropTypes.func,
    };

    static defaultProps = {
        onClose: () => {}
    };

    state = {
        occurrencesVisible: false
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

    renderActionButtons = (canCancel, canReject, showAccept) => (
        <Modal.Actions>
            {canCancel && (
                <Button type="button"
                        icon="remove circle"
                        size="small"
                        content={<Translate>Cancel booking</Translate>} />
            )}
            {canReject && (
                <Button type="button"
                        icon="remove circle"
                        color="red"
                        size="small"
                        content={<Translate>Reject booking</Translate>} />
            )}
            {showAccept && (
                <Button type="button"
                        icon="check circle"
                        color="green"
                        size="small"
                        content={<Translate>Accept booking</Translate>} />
            )}
        </Modal.Actions>
    );

    renderBookingStatus = ({isPending, isAccepted, isCancelled, isRejected}) => {
        let color, status;

        if (isPending) {
            color = 'yellow';
            status = Translate.string('Pending Confirmation');
        } else if (isCancelled) {
            color = 'grey';
            status = Translate.string('Cancelled');
        } else if (isRejected) {
            color = 'red';
            status = Translate.string('Rejected');
        } else if (isAccepted) {
            color = 'green';
            status = Translate.string('Valid');
        }

        return (
            <Label color={color}>
                {status}
            </Label>
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
        booking: bookingsSelectors.getDetailsWithRoom(state, {bookingId})
    })
)(BookingDetailsModal);
