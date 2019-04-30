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

import React, {useState} from 'react';
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import {Button, Confirm, Item} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import SpriteImage from '../../components/SpriteImage';
import {RoomEditModal} from '../../common/rooms';
import * as adminActions from './actions';

import './AdminRoomItem.module.scss';


function AdminRoomItem({room, deleteRoom}) {
    const [editing, setEditing] = useState(false);
    const [deleting, setDeleting] = useState(false);

    return (
        <Item key={room.id} styleName="room-item">
            <Item.Image size="small" styleName="room-item-image">
                <SpriteImage pos={room.spritePosition}
                             width="100%"
                             height="100%" />
            </Item.Image>
            <Item.Content>
                <Item.Header styleName="room-item-header">
                    {room.fullName}
                    <div>
                        <Button size="mini" icon="pencil" circular onClick={() => setEditing(true)} />
                        <Button size="mini" icon="trash" negative circular onClick={() => setDeleting(true)} />
                    </div>
                </Item.Header>
                <Item.Meta>{room.ownerName}</Item.Meta>
                <Item.Description>
                    {room.comments}
                </Item.Description>
            </Item.Content>
            {editing && (
                <RoomEditModal roomId={room.id} onClose={() => setEditing(false)} />
            )}
            <Confirm header={Translate.string('Confirm deletion')}
                     content={Translate.string('Are you sure you want to delete this room?')}
                     confirmButton={<Button content={Translate.string('Delete')} negative />}
                     cancelButton={Translate.string('Cancel')}
                     open={deleting}
                     onCancel={() => setDeleting(false)}
                     onConfirm={() => deleteRoom(room.id)} />

        </Item>
    );
}

AdminRoomItem.propTypes = {
    room: PropTypes.object.isRequired,
    deleteRoom: PropTypes.func.isRequired,
};

export default connect(
    null,
    {deleteRoom: adminActions.deleteRoom}
)(AdminRoomItem);
