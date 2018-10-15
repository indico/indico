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
import PropTypes from 'prop-types';
import {Button, Modal, Message, Grid, Header, Icon, Popup, List} from 'semantic-ui-react';
import {Param, Translate} from 'indico/react/i18n';
import {toMoment, serializeDate} from 'indico/utils/date';
import BookingTimeInformation from '../../components/TimeInformation';
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
        const {booking: {attributes: {room}}} = this.props;
        return (occurrences) => ({
            availability: {
                bookings: occurrences[day].map((candidate) => ({...candidate, bookable: false})) || [],
            },
            label: moment(day).format('L'),
            key: day,
            room
        });
    }

    renderTimeline = (occurrences, dateRange) => {
        const hourSeries = _.range(6, 24, 2);
        const rows = dateRange.map((day) => this._getRowSerializer(day)(occurrences));
        return <DailyTimelineContent rows={rows} hourSeries={hourSeries} />;
    };

    renderBookingHistory = (editLogs, createdOn, createdBy) => {
        const items = (editLogs ? editLogs.map((log, i) => {
            const {timestamp, info, userName} = log;
            const basicInfo = <strong>{info[0]}</strong>;
            const details = (info[1] ? info[1] : null);
            const dateValue = serializeDate(toMoment(timestamp), 'L');
            const date = <Param name="date" value={dateValue} wrapper={<span styleName="log-date" />} />;
            const mainInfo = <Param name="details" value={basicInfo} />;
            const user = <Param name="user" value={userName} />;
            if (details) {
                const popupContent = <Param name="details" wrapper={<span styleName="popup-center" />} value={details} />;
                const wrapper = <PopupParam content={<Translate>{popupContent}</Translate>} />;
                const popupInfo = <Param name="info" wrapper={wrapper} value={basicInfo} />;
                return (
                    <List.Item key={i}>
                        <Translate>{date} - {popupInfo} by {user}</Translate>
                    </List.Item>
                );
            }
            return (
                <List.Item key={i}>
                    <Translate>{date} - {mainInfo} by {user}</Translate>
                </List.Item>
            );
        }) : null);
        const bookingCreatedDate = <Param name="date" value={createdOn} wrapper={<span styleName="log-date" />} />;
        const bookingCreatedBy = <Param name="created-by" value={createdBy} />;
        const bookingCreatedInfo = <Param name="created-info" value={<strong>Booking created </strong>} />;
        return (
            <div styleName="booking-logs">
                <Header><Translate>Booking history</Translate></Header>
                <List divided styleName="log-list">
                    {items}
                    <List.Item>
                        <Translate>
                            {bookingCreatedDate} - {bookingCreatedInfo} by {bookingCreatedBy}
                        </Translate>
                    </List.Item>
                </List>
            </div>
        );
    };

    render() {
        const {booking} = this.props;
        const {
            room, bookedForUser, startDt, endDt, repetition, createdByUser, createdDt, bookingReason
        } = booking.attributes;
        const {occurrences, dateRange, editLogs} = booking;
        const {occurrencesVisible} = this.state;
        const {fullName: bookedForName, email: bookedForEmail, phone: bookedForPhone} = bookedForUser;
        const dates = {startDate: startDt, endDate: endDt};
        const createdOn = serializeDate(toMoment(createdDt));
        const times = {startTime: moment(startDt).utc().format('HH:mm'), endTime: moment(endDt).utc().format('HH:mm')};
        const recurrence = this.getRecurrence(repetition);
        const legendLabels = [
            {label: Translate.string('Occurrence'), color: 'orange'},
        ];
        return (
            <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                <Modal.Header styleName="booking-modal-header">
                    <Translate>Booking Details</Translate>
                    <span>
                        <Button icon="pencil" circular />
                        <Button icon="trash" circular />
                    </span>
                </Modal.Header>
                <Modal.Content>
                    <Grid columns={2}>
                        <Grid.Column>
                            <RoomBasicDetails room={room} />
                            <RoomKeyLocation room={room} />
                            <BookingTimeInformation recurrence={recurrence}
                                                    dates={dates}
                                                    timeSlot={times} />
                            <Button attached="bottom" color="blue" fluid onClick={() => this.setState({occurrencesVisible: true})}>
                                <Translate>Consult the booking occurrences</Translate>
                            </Button>
                        </Grid.Column>
                        <Grid.Column>
                            <Header><Icon name="user" /><Translate>Booked for</Translate></Header>
                            <div>{bookedForName}</div>
                            {bookedForPhone && <div><Icon name="phone" />{bookedForPhone}</div>}
                            {bookedForEmail && <div><Icon name="mail" />{bookedForEmail}</div>}
                            <Message info icon styleName="message-icon">
                                <Icon name="info" />
                                <Message.Content>
                                    <Message.Header>
                                        <Translate>Booking reason: </Translate>
                                    </Message.Header>
                                    {bookingReason}
                                </Message.Content>
                            </Message>
                            {this.renderBookingHistory(editLogs, createdOn, createdByUser)}
                            <div styleName="action-buttons">
                                <Button type="button" icon="cancel" content={<Translate>Cancel booking</Translate>} />
                                <Button type="button" icon="cancel" color="red" content={<Translate>Reject booking</Translate>} />
                            </div>
                        </Grid.Column>
                    </Grid>
                </Modal.Content>
                <Modal open={occurrencesVisible}
                       onClose={() => this.setState({occurrencesVisible: false})}
                       size="large" closeIcon>
                    <Modal.Header className="legend-header">
                        <Translate>Occurrences</Translate>
                        <Popup trigger={<Icon name="info circle" className="legend-info-icon" />}
                               content={<TimelineLegend labels={legendLabels} compact />} />
                    </Modal.Header>
                    <Modal.Content scrolling>
                        {occurrences && this.renderTimeline(occurrences, dateRange)}
                    </Modal.Content>
                </Modal>
            </Modal>
        );
    }
}

const mapStateToProps = (state, {bookingId}) => ({
    booking: bookingsSelectors.getDetailsWithRoom(state, {bookingId})
});

export default connect(
    mapStateToProps,
)(BookingDetailsModal);
