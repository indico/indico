// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {connect} from 'react-redux';
import {Button, Confirm, Item} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {RoomEditModal} from '../../common/rooms';
import SpriteImage from '../../components/SpriteImage';

import * as adminActions from './actions';

import './AdminRoomItem.module.scss';

function AdminRoomItem({room, locationId, deleteRoom, fetchRooms}) {
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleCloseModal = saved => {
    if (saved) {
      fetchRooms();
    }
    setEditing(false);
  };

  return (
    <Item key={room.id} styleName="room-item">
      <Item.Image size="small" styleName="room-item-image">
        <SpriteImage pos={room.spritePosition} width="100%" height="100%" />
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
        <Item.Description>{room.comments}</Item.Description>
      </Item.Content>
      {editing && (
        <RoomEditModal roomId={room.id} locationId={locationId} onClose={handleCloseModal} />
      )}
      <Confirm
        header={Translate.string('Confirm deletion')}
        content={Translate.string('Are you sure you want to delete this room?')}
        confirmButton={<Button content={Translate.string('Delete')} negative />}
        cancelButton={Translate.string('Cancel')}
        open={deleting}
        onCancel={() => setDeleting(false)}
        onConfirm={() => deleteRoom(room.id)}
      />
    </Item>
  );
}

AdminRoomItem.propTypes = {
  room: PropTypes.object.isRequired,
  locationId: PropTypes.number.isRequired,
  deleteRoom: PropTypes.func.isRequired,
  fetchRooms: PropTypes.func.isRequired,
};

export default connect(
  null,
  {
    deleteRoom: adminActions.deleteRoom,
    fetchRooms: adminActions.fetchRooms,
  }
)(AdminRoomItem);
