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
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import roomsSpriteURL from 'indico-url:rooms_new.sprite';
import {Grid, Header, Icon, Popup} from 'semantic-ui-react';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import SpriteImage from './SpriteImage';
import {selectors as configSelectors} from '../common/config';

import './RoomBasicDetails.module.scss';


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

function RoomBasicDetails({room, roomsSpriteToken}) {
    const {
        owner_name: owner, latitude, longitude, division, location_name: location, surface_area: surface, capacity,
        telephone, full_name: name
    } = room;
    return (
        <Grid columns={2}>
            <Grid.Column textAlign="center">
                <SpriteImage src={roomsSpriteURL({version: roomsSpriteToken})} pos={room.sprite_position}
                             origin="0"
                             scale="0.85" />
                <RoomEquipmentBox room={room} />
            </Grid.Column>
            <Grid.Column>
                <Header>
                    {name}
                    <Header.Subheader>{division}</Header.Subheader>
                </Header>
                <div>{location}</div>
                {owner && (<><Translate>Owner</Translate>: {owner}</>)}
                {latitude && (
                    <div>
                        <Icon name="location arrow" /> {latitude}, {longitude}
                    </div>
                )}
                {telephone && <div><Icon name="phone" /> {room.telephone}</div>}
                {capacity && (
                    <div>
                        <PluralTranslate count={capacity}>
                            <Singular>
                                1 seat
                            </Singular>
                            <Plural>
                                <Param name="count" value={capacity} /> seats
                            </Plural>
                        </PluralTranslate>
                    </div>
                )}
                {surface && <div>{surface}m²</div>}
            </Grid.Column>
        </Grid>
    );
}

RoomBasicDetails.propTypes = {
    room: PropTypes.object.isRequired,
    roomsSpriteToken: PropTypes.string.isRequired,
};


export default connect(
    state => ({
        roomsSpriteToken: configSelectors.getRoomsSpriteToken(state),
    })
)(RoomBasicDetails);
