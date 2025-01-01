// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import RoomDetailsModal from './RoomDetailsModal';
import RoomDetailsPreloader from './RoomDetailsPreloader';

export default {
  /* eslint-disable react/display-name */
  'room-details': (onClose, roomId) => (
    <RoomDetailsPreloader roomId={roomId}>
      {() => <RoomDetailsModal roomId={roomId} onClose={onClose} promptDatesOnBook />}
    </RoomDetailsPreloader>
  ),
  'room-details-book': (onClose, roomId) => (
    <RoomDetailsPreloader roomId={roomId}>
      {() => <RoomDetailsModal roomId={roomId} onClose={onClose} />}
    </RoomDetailsPreloader>
  ),
};
