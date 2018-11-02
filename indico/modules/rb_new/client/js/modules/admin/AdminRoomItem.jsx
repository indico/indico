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
import {connect} from 'react-redux';
import {Button, Item} from 'semantic-ui-react';
import roomsSpriteURL from 'indico-url:rooms_new.sprite';
import SpriteImage from '../../components/SpriteImage';
import {selectors as configSelectors} from '../../common/config';

import './AdminRoomItem.module.scss';


function AdminRoomItem({roomsSpriteToken, room}) {
    return (
        <Item key={room.id} styleName="room-item">
            <Item.Image size="small" styleName="room-item-image">
                <SpriteImage src={roomsSpriteURL({version: roomsSpriteToken})}
                             pos={room.spritePosition}
                             origin="0 0"
                             scale="0.5" />
            </Item.Image>
            <Item.Content>
                <Item.Header styleName="room-item-header">
                    {room.fullName}
                    <div>
                        <Button size="mini" icon="pencil" circular />
                        <Button size="mini" icon="trash" negative circular />
                    </div>
                </Item.Header>
                <Item.Meta>{room.ownerName}</Item.Meta>
                <Item.Description>
                    {room.comments}
                </Item.Description>
            </Item.Content>
        </Item>
    );
}

AdminRoomItem.propTypes = {
    roomsSpriteToken: PropTypes.string.isRequired,
    room: PropTypes.object.isRequired,
};

export default connect(
    state => ({
        roomsSpriteToken: configSelectors.getRoomsSpriteToken(state),
    }),
)(AdminRoomItem);
