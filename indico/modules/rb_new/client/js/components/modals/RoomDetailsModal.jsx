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

import {push} from 'connected-react-router';
import React from 'react';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import {Button, Grid, Icon, Modal, Header, Message, List, Segment} from 'semantic-ui-react';

import {Translate, Param} from 'indico/react/i18n';

import {RoomBasicDetails} from '../RoomBasicDetails';
import TimelineContent from '../TimelineContent';

import './RoomDetailsModal.module.scss';


class RoomDetailsModal extends React.Component {
    static propTypes = {
        roomDetails: PropTypes.object,
        onClose: PropTypes.func,
        bookRoom: PropTypes.func.isRequired
    };

    static defaultProps = {
        roomDetails: null,
        onClose: () => {}
    };

    handleCloseModal = () => {
        const {onClose} = this.props;
        onClose();
    };

    render() {
        const {bookRoom, roomDetails} = this.props;
        if (!roomDetails) {
            return null;
        }
        return (
            <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                <Modal.Header styleName="room-details-header">
                    <Translate>Room Details</Translate>
                    <span>
                        <Button icon="pencil" circular />
                    </span>
                </Modal.Header>
                <Modal.Content>
                    <RoomDetails room={roomDetails} bookRoom={bookRoom} />
                </Modal.Content>
            </Modal>
        );
    }
}

export default (namespace) => {
    const mapStateToProps = state => ({
        equipmentTypes: state.equipment.types,
        ...state[namespace].filters,
        hasOwnedRooms: state.user.hasOwnedRooms,
        hasFavoriteRooms: Object.values(state.user.favoriteRooms).some(fr => fr),
        namespace
    });

    const mapDispatchToProps = dispatch => ({
        bookRoom(room) {
            if (namespace === 'roomList') {
                dispatch(push(`/rooms/${room.id}/book`));
            } else {
                dispatch(push(`/book/${room.id}/confirm`));
            }
        }
    });

    return connect(
        mapStateToProps,
        mapDispatchToProps
    )(RoomDetailsModal);
};

function RoomDetails({bookRoom, room}) {
    const minHour = 6;
    const maxHour = 22;
    const step = 2;
    const hourSeries = _.range(minHour, maxHour + step, step);

    return (
        <div styleName="room-details">
            <Grid columns={2}>
                <Grid.Column>
                    <div>
                        <RoomBasicDetails room={room} />
                        <RoomAvailabilityBox room={room} />
                        <RoomCommentsBox room={room} />
                        <RoomKeyLocationBox room={room} />
                        <RoomCustomAttributesBox room={room} />
                    </div>
                </Grid.Column>
                <Grid.Column>
                    <Header><Translate>Usage</Translate></Header>
                    <TimelineContent rows={room.bookings}
                                     hourSeries={hourSeries} />
                    <Header><Translate>Statistics</Translate></Header>
                    <Message attached info>
                        <Icon name="info" />
                        <Translate>Would you like to use this room?</Translate>
                    </Message>
                    <Segment attached="bottom">
                        <Button color="green" onClick={() => bookRoom(room)}>
                            <Icon name="check circle" />
                            <Translate>Book it</Translate>
                        </Button>
                    </Segment>
                </Grid.Column>
            </Grid>
        </div>
    );
}

RoomDetails.propTypes = {
    bookRoom: PropTypes.func.isRequired,
    room: PropTypes.object.isRequired,
};

function RoomAvailabilityBox({room}) {
    return (
        room.is_public ? (
            <Message positive styleName="message-icon" icon="unlock" content={
                <>
                    <p><Translate>Anyone can book this room.</Translate></p>
                    {room.max_advance_days && (
                        <p>
                            <Translate>
                                Max. <Param name="max_advance_days" value={room.max_advance_days} /> days in advance
                            </Translate>
                        </p>
                    )}
                </>
            } />
        ) : (
            <Message negative styleName="message-icon" icon="lock"
                     content={Translate.string('This room is not publicly available.')} />
        )
    );
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

function RoomKeyLocationBox({room}) {
    return room.key_location && (
        <Message styleName="message-icon" icon="key"
                 content={<span dangerouslySetInnerHTML={{__html: room.key_location}} />} />
    );
}

RoomKeyLocationBox.propTypes = {
    room: PropTypes.object.isRequired,
};

function RoomCustomAttributesBox({room}) {
    return (
        !!room.attributes.length && (
            <Message>
                <List>
                    {room.attributes.map(({title, value}) => (
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
    room: PropTypes.object.isRequired,
};
