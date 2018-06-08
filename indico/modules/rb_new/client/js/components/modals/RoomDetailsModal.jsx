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
import {Button, Grid, Modal, Image, Header, Message, Icon, List, Popup} from 'semantic-ui-react';

import {Translate, Param} from 'indico/react/i18n';

import './RoomDetailsModal.module.scss';


export default class RoomDetailsModal extends React.Component {
    static propTypes = {
        roomDetails: PropTypes.shape({
            list: PropTypes.array,
            isFetching: PropTypes.bool,
            currentViewID: PropTypes.number,
        }).isRequired,
        setRoomDetailsModal: PropTypes.func.isRequired,
    };

    handleCloseModal = () => {
        const {setRoomDetailsModal} = this.props;
        setRoomDetailsModal(null);
    };

    render() {
        const {roomDetails: {rooms, currentViewID}} = this.props;
        if (!(currentViewID in rooms)) {
            return null;
        }
        const room = rooms[currentViewID];
        return (
            <Modal open onClose={this.handleCloseModal}>
                <Modal.Header styleName="room-details-header">
                    <Translate>Room Details</Translate>
                    <span>
                        <Button icon="pencil" circular />
                    </span>
                </Modal.Header>
                <Modal.Content>
                    <RoomDetails room={room} />
                </Modal.Content>
            </Modal>
        );
    }
}

function RoomDetails({room}) {
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
                    <Header><Translate>Statistics</Translate></Header>
                </Grid.Column>
            </Grid>
        </div>
    );
}

RoomDetails.propTypes = {
    room: PropTypes.object.isRequired,
};

export function RoomBasicDetails({room}) {
    return (
        <Grid columns={2}>
            <Grid.Column textAlign="center">
                <Image src={room.large_photo_url} />
                <RoomEquipmentBox room={room} />
            </Grid.Column>
            <Grid.Column>
                <Header>
                    {room.full_name}
                    <Header.Subheader>{room.division}</Header.Subheader>
                </Header>
                <div>{room.location_name}</div>
                <Translate>Owner</Translate>: {room.owner_name}
                <div>
                    <Icon name="location arrow" /> {room.latitude}, {room.longitude}
                </div>
                {room.telephone && <div><Icon name="phone" /> {room.telephone}</div>}
                {room.capacity && <div>{room.capacity} <Translate>seats</Translate></div>}
                {room.surface_area && <div>{room.surface_area}m²</div>}
            </Grid.Column>
        </Grid>
    );
}

RoomBasicDetails.propTypes = {
    room: PropTypes.object.isRequired,
};

function RoomEquipmentBox({room}) {
    return (
        <div styleName="equipment-box">
            {room.has_vc && (
                <Popup trigger={<Icon name="video camera" color="teal" size="large" />}
                       content={Translate.string('Videoconference available')} />
            )}
            {room.has_webcast_recording && (
                <Popup trigger={<Icon name="podcast" color="teal" size="large" />}
                       content={Translate.string('Webcast recording available')} />
            )}
            {room.has_projector && (
                <Popup trigger={<Icon name="film" color="teal" size="large" />}
                       content={Translate.string('Projector available')} />
            )}
        </div>
    );
}

RoomEquipmentBox.propTypes = {
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
