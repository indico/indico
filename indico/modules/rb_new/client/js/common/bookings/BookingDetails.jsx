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
import {Grid, Header, Icon, List, Message, Modal, Popup} from 'semantic-ui-react';

import {toMoment, serializeDate} from 'indico/utils/date';
import {Param, Translate} from 'indico/react/i18n';
import {DailyTimelineContent, TimelineLegend} from '../timeline';
import {getRecurrenceInfo, PopupParam} from '../../util';
import RoomBasicDetails from '../../components/RoomBasicDetails';
import RoomKeyLocation from '../../components/RoomKeyLocation';
import TimeInformation from '../../components/TimeInformation';
import BookingEventLink from './BookingEventLink';

import './BookingDetails.module.scss';


export default class BookingDetails extends React.Component {
    static propTypes = {
        booking: PropTypes.object.isRequired,
    };

    state = {
        occurrencesVisible: false,
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
        return (occurrences) => ({
            availability: {
                bookings: occurrences[day].map((candidate) => ({...candidate, bookable: false})) || [],
            },
            label: moment(day).format('L'),
            key: day,
            room
        });
    };

    renderTimeline = (occurrences, dateRange) => {
        const rows = dateRange.map((day) => this._getRowSerializer(day)(occurrences));
        return <DailyTimelineContent rows={rows} fixedHeight={rows.length > 1 ? '70vh' : null} />;
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

    render() {
        const {occurrencesVisible} = this.state;
        const {
            booking: {
                id, startDt, endDt, occurrences, dateRange, repetition, room, bookedForUser, isLinkedToEvent,
                bookingReason, editLogs, createdDt, createdByUser
            }
        } = this.props;
        const legendLabels = [{label: Translate.string('Occurrence'), color: 'orange'}];
        const dates = {startDate: startDt, endDate: endDt};
        const times = {startTime: moment(startDt).format('HH:mm'), endTime: moment(endDt).format('HH:mm')};
        const recurrence = getRecurrenceInfo(repetition);

        return (
            <>
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
                        <>
                            {bookedForUser && this.renderBookedFor(bookedForUser)}
                            {this.renderReason(bookingReason)}
                            {isLinkedToEvent && <BookingEventLink bookingId={id} />}
                            {this.renderBookingHistory(editLogs, createdDt, createdByUser)}
                        </>
                    </Grid.Column>
                </Grid>
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
