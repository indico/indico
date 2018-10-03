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
import {Button, Modal, Message, Grid, Header, ModalActions, Icon, Popup, List} from 'semantic-ui-react';
import {Param, Translate} from 'indico/react/i18n';
import {toMoment, serializeDate} from 'indico/utils/date';
import BookingTimeInformation from '../BookingTimeInformation';
import RoomBasicDetails from '../../components/RoomBasicDetails';
import {selectors as bookingsSelectors} from '../../common/bookings';
import TimelineContent from '../../components/TimelineContent';
import TimelineLegend from '../../components/TimelineLegend';
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
                candidates: occurrences[day].map((candidate) => ({...candidate, bookable: false})) || [],
            },
            label: moment(day).format('L'),
            key: day,
            room
        });
    }

    renderTimeline = (occurrences, dateRange) => {
        const hourSeries = _.range(6, 24, 2);
        const rows = dateRange.map((day) => this._getRowSerializer(day)(occurrences));
        return <TimelineContent rows={rows} hourSeries={hourSeries} />;
    };

    renderBookingHistory = (editLogs, createdOn, createdBy) => {
        const items = (editLogs ? editLogs.map((log, i) => {
            const {timestamp, info, user_name: userName} = log;
            const basicInfo = <strong>{info[0]}</strong>;
            const details = (info[1] ? info[1] : null);
            const dateValue = serializeDate(toMoment(timestamp));
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
            <div>
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
            room, booked_for_user: bookedFor, start_dt: startDt, end_dt: endDt, repetition, created_by_user: createdBy,
            created_dt: createdDt, booking_reason: reason
        } = booking.attributes;
        const {occurrences, date_range: dateRange, edit_logs: editLogs} = booking;
        const {occurrencesVisible} = this.state;
        const {full_name: bookedForName, email: bookedForEmail, phone: bookedForPhone} = bookedFor;
        const dates = {startDate: startDt, endDate: endDt};
        const createdOn = serializeDate(toMoment(createdDt));
        const times = {startTime: moment(startDt).utc().format('HH:mm'), endTime: moment(endDt).utc().format('HH:mm')};
        const recurrence = this.getRecurrence(repetition);
        const link = <a onClick={() => this.setState({occurrencesVisible: true})} />;
        const legendLabels = [
            {label: Translate.string('Occurrence'), color: 'green'},
        ];
        return (
            <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                <Modal.Header>
                    <Translate>Booking Details</Translate>
                </Modal.Header>
                <Modal.Content>
                    <Grid columns={2}>
                        <Grid.Column>
                            <RoomBasicDetails room={room} />
                            <BookingTimeInformation recurrence={recurrence}
                                                    dates={dates}
                                                    timeSlot={times} />
                            <Message attached="bottom">
                                <Message.Content>
                                    <Translate>
                                        Consult the <Param name="occurrences-link" wrapper={link}>timeline view</Param> to see the booking occurrences.
                                    </Translate>
                                </Message.Content>
                            </Message>
                        </Grid.Column>
                        <Grid.Column>
                            <Grid>
                                <Grid.Column width={8}>
                                    <Header><Icon name="user" /><Translate>Booked for</Translate></Header>
                                    <div>{bookedForName}</div>
                                    {bookedForPhone && <div><Icon name="phone" />{bookedForPhone}</div>}
                                    {bookedForEmail && <div><Icon name="mail" />{bookedForEmail}</div>}
                                </Grid.Column>
                                <Grid.Column width={8}>
                                    <Header><Translate>Reason</Translate></Header>
                                    <div>{reason}</div>
                                </Grid.Column>
                                {this.renderBookingHistory(editLogs, createdOn, createdBy)}
                            </Grid>
                        </Grid.Column>
                    </Grid>
                </Modal.Content>
                <ModalActions>
                    <Button type="button" content={Translate.string('Cancel')} />
                    <Button type="button" content={Translate.string('Reject')} />
                    <Button type="button" content={Translate.string('Modify')} />
                    <Button type="button" content={Translate.string('Delete')} />
                    <Button type="button" content={Translate.string('Clone')} />
                    <Modal open={occurrencesVisible}
                           onClose={() => this.setState({occurrencesVisible: false})}
                           size="large" closeIcon>
                        <Modal.Header className="legend-header">
                            <Translate>Bookings</Translate>
                            <Popup trigger={<Icon name="info circle" className="legend-info-icon" />}
                                   content={<TimelineLegend labels={legendLabels} compact />} />
                        </Modal.Header>
                        <Modal.Content scrolling>
                            {occurrences && this.renderTimeline(occurrences, dateRange)}
                        </Modal.Content>
                    </Modal>
                </ModalActions>
            </Modal>
        );
    }
}

const mapStateToProps = (state, {bookingId}) => ({
    booking: bookingsSelectors.getDetails(state, {bookingId})
});

export default connect(
    mapStateToProps,
)(BookingDetailsModal);
