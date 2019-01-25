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
import {bindActionCreators} from 'redux';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import {Button, Grid, Icon, Modal, Header, Message, List, Segment, Popup} from 'semantic-ui-react';
import {Translate, Param} from 'indico/react/i18n';
import {Overridable, IndicoPropTypes} from 'indico/react/util';
import RoomBasicDetails from '../../components/RoomBasicDetails';
import RoomKeyLocation from '../../components/RoomKeyLocation';
import RoomStats from './RoomStats';
import {DailyTimelineContent, TimelineLegend} from '../timeline';
import * as roomsSelectors from './selectors';
import {actions as bookRoomActions} from '../../modules/bookRoom';

import './RoomDetailsModal.module.scss';


class RoomDetailsModal extends React.Component {
    static propTypes = {
        room: PropTypes.object.isRequired,
        availability: PropTypes.array.isRequired,
        attributes: PropTypes.array.isRequired,
        onClose: PropTypes.func.isRequired,
        promptDatesOnBook: PropTypes.bool,
        title: IndicoPropTypes.i18n,
        actions: PropTypes.exact({
            openBookRoom: PropTypes.func.isRequired,
            openBookingForm: PropTypes.func.isRequired,
        }).isRequired,
    };

    static defaultProps = {
        promptDatesOnBook: false,
        title: <Translate>Room Details</Translate>,
    };

    handleCloseModal = () => {
        const {onClose} = this.props;
        onClose();
    };

    render() {
        const {
            room, availability, attributes, promptDatesOnBook, title,
            actions: {openBookRoom, openBookingForm}
        } = this.props;
        return (
            <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                <Modal.Header styleName="room-details-header">
                    {title}
                    <span>
                        <Button icon="pencil" circular />
                    </span>
                </Modal.Header>
                <Modal.Content>
                    <RoomDetails room={room}
                                 attributes={attributes}
                                 availability={availability}
                                 bookRoom={promptDatesOnBook ? openBookRoom : openBookingForm} />
                </Modal.Content>
            </Modal>
        );
    }
}

export default connect(
    (state, {roomId}) => ({
        room: roomsSelectors.getRoom(state, {roomId}),
        availability: roomsSelectors.getAvailability(state, {roomId}),
        attributes: roomsSelectors.getAttributes(state, {roomId}),
    }),
    dispatch => ({
        actions: bindActionCreators({
            openBookRoom: bookRoomActions.openBookRoom,
            openBookingForm: bookRoomActions.openBookingForm,
        }, dispatch),
    }),
)(Overridable.component('RoomDetailsModal', RoomDetailsModal));


function RoomDetails({bookRoom, room, availability, attributes}) {
    const legendLabels = [
        {label: Translate.string('Booked'), color: 'orange', style: 'booking'},
        {label: Translate.string('Pre-Booking'), style: 'pre-booking'},
        {label: Translate.string('Blocked'), style: 'blocking'},
        {label: Translate.string('Not bookable'), style: 'unbookable'}
    ];

    const rowSerializer = ({bookings, nonbookablePeriods, unbookableHours, blockings, day}) => ({
        availability: {
            bookings: bookings || [],
            nonbookablePeriods: nonbookablePeriods || [],
            unbookableHours: unbookableHours || [],
            blockings: blockings || []
        },
        label: moment(day).format('L'),
        conflictIndicator: false,
        key: day,
        room
    });

    return (
        <div styleName="room-details">
            <Grid columns={2}>
                <Grid.Column>
                    <div>
                        <RoomBasicDetails room={room} />
                        <RoomAvailabilityBox room={room} />
                        <RoomCommentsBox room={room} />
                        <RoomKeyLocation room={room} />
                        <RoomCustomAttributesBox attributes={attributes} />
                    </div>
                </Grid.Column>
                <Grid.Column>
                    <Header className="legend-header">
                        <Translate>Usage</Translate>
                        <Popup trigger={<Icon name="info circle" className="legend-info-icon" />}
                               content={<TimelineLegend labels={legendLabels} compact />} />
                    </Header>
                    <DailyTimelineContent rows={availability.map(rowSerializer)} />
                    <RoomStats roomId={room.id} />
                    {(room.canUserBook || room.canUserPrebook) && (
                        <>
                            <Message attached info>
                                <Icon name="info" />
                                <Translate>Would you like to use this space?</Translate>
                            </Message>
                            <Segment attached="bottom">
                                {room.canUserBook && (
                                    <Button color="green" onClick={() => bookRoom(room.id, {isPrebooking: false})}>
                                        <Icon name="check circle" />
                                        <Translate>Start booking</Translate>
                                    </Button>
                                )}
                                {room.canUserPrebook && (
                                    <Button color="orange" onClick={() => bookRoom(room.id, {isPrebooking: true})}>
                                        <Icon name="check circle" />
                                        <Translate>Start pre-booking</Translate>
                                    </Button>
                                )}
                            </Segment>
                        </>
                    )}
                </Grid.Column>
            </Grid>
        </div>
    );
}

RoomDetails.propTypes = {
    bookRoom: PropTypes.func.isRequired,
    room: PropTypes.object.isRequired,
    availability: PropTypes.array.isRequired,
    attributes: PropTypes.array.isRequired,
};


function RoomAvailabilityBox({room}) {
    if (room.canUserBook || room.canUserPrebook) {
        return (
            <Message positive styleName="message-icon" icon="unlock" content={
                <>
                    <p>
                        {room.isPublic ? (
                            <Translate>Anyone can book this space.</Translate>
                        ) : (
                            <Translate>You can book this space.</Translate>
                        )}
                    </p>
                    {room.maxAdvanceDays && (
                        <p>
                            <Translate>
                                Max. <Param name="max_advance_days" value={room.maxAdvanceDays} /> days in advance
                            </Translate>
                        </p>
                    )}
                </>
            } />
        );
    } else if (!room.isReservable) {
        return (
            <Message negative styleName="message-icon" icon="exclamation triangle"
                     content={Translate.string('This space cannot be booked at the moment.')} />
        );
    } else {
        return (
            <Message negative styleName="message-icon" icon="lock"
                     content={Translate.string('You are not authorized to book this space.')} />
        );
    }
}

RoomAvailabilityBox.propTypes = {
    room: PropTypes.object.isRequired,
};

function RoomCommentsBox({room}) {
    return room.comments && (<Message styleName="message-icon" icon="info" content={room.comments} info />);
}

RoomCommentsBox.propTypes = {
    room: PropTypes.object.isRequired,
};

function RoomCustomAttributesBox({attributes}) {
    return (
        !!attributes.length && (
            <Message>
                <List>
                    {attributes.map(({title, value}) => (
                        <List.Item key={title}>
                            <span styleName="attribute-title"><strong>{title}</strong></span>
                            <span>{value}</span>
                        </List.Item>
                    ))}
                </List>
            </Message>
        )
    );
}

RoomCustomAttributesBox.propTypes = {
    attributes: PropTypes.arrayOf(PropTypes.shape({
        title: PropTypes.string.isRequired,
        value: PropTypes.string.isRequired,
    })).isRequired,
};
