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
import {Button, Modal, Message, Grid, Header, ModalActions, Icon} from 'semantic-ui-react';
import {Param, Translate} from 'indico/react/i18n';
import {toMoment, serializeDate} from 'indico/utils/date';
import BookingTimeInformation from '../BookingTimeInformation';
import RoomBasicDetails from '../../components/RoomBasicDetails';
import {selectors as bookingsSelectors} from '../../common/bookings';

import './BookingDetailsModal.module.scss';


class BookingDetailsModal extends React.Component {
    static propTypes = {
        booking: PropTypes.object.isRequired,
        onClose: PropTypes.func,
    };

    static defaultProps = {
        onClose: () => {}
    };

    handleCloseModal = () => {
        const {onClose} = this.props;
        onClose();
    };

    render() {
        const {booking} = this.props;
        return (
            <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                <Modal.Header>
                    <Translate>Booking Details</Translate>
                </Modal.Header>
                <Modal.Content>
                    <BookingDetails booking={booking} />
                </Modal.Content>
                <ModalActions>
                    <Button type="button" content={Translate.string('Cancel')} />
                    <Button type="button" content={Translate.string('Reject')} />
                    <Button type="button" content={Translate.string('Modify')} />
                    <Button type="button" content={Translate.string('Delete')} />
                    <Button type="button" content={Translate.string('Clone')} />
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

BookingDetails.propTypes = {
    booking: PropTypes.object.isRequired
};

function BookingDetails({booking}) {
    const {
        room, booked_for_user: bookedFor, start_dt: startDt, end_dt: endDt, repetition,
        created_by_user: createdBy, created_dt: createdDt, booking_reason: reason
    } = booking;
    const {full_name: bookedForName, email: bookedForEmail, phone: bookedForPhone} = bookedFor;
    const dates = {startDate: startDt, endDate: endDt};
    const createdOn = serializeDate(toMoment(createdDt));
    const times = {startTime: moment(startDt).utc().format('HH:mm'), endTime: moment(endDt).utc().format('HH:mm')};
    const recurrence = getRecurrence(repetition);
    return (
        <div>
            <Grid columns={2}>
                <Grid.Column>
                    <RoomBasicDetails room={room} />
                    <BookingTimeInformation recurrence={recurrence}
                                            dates={dates}
                                            timeSlot={times} />
                    <Message attached="bottom">
                        <Message.Content>
                            <Translate>
                                Consult the timeline view to see the booking occurrences.
                            </Translate>
                        </Message.Content>
                    </Message>
                </Grid.Column>
                <Grid.Column>
                    <Grid columns={2}>
                        <Grid.Column>
                            <Header><Icon name="user" /><Translate>Booked for</Translate></Header>
                            <div>{bookedForName}</div>
                            {bookedForPhone && <div><Icon name="phone" />{bookedForPhone}</div>}
                            {bookedForEmail && <div><Icon name="mail" />{bookedForEmail}</div>}
                        </Grid.Column>
                        <Grid.Column>
                            <Header><Translate>Reason</Translate></Header>
                            <div>{reason}</div>
                        </Grid.Column>
                    </Grid>
                    <Header>Booking history</Header>
                    <div>
                        <Translate>
                            <Param name="date" value={createdOn} /> - booking created by <Param name="created_by" value={createdBy} />
                        </Translate>
                    </div>
                </Grid.Column>
            </Grid>
        </div>
    );
}

function getRecurrence(repetition) {
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
}
