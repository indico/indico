// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {filterDTHandler} from '../../serializers';

export const ajax = {
  timeframe: {
    onlyIf: ({timeframe}) => !!timeframe,
    serializer: ({timeframe}) => timeframe,
  },
  my_rooms: {
    onlyIf: ({myRooms}) => myRooms,
    serializer: ({myRooms}) => myRooms,
  },
  mine: {
    onlyIf: ({myBlockings}) => myBlockings,
    serializer: ({myBlockings}) => myBlockings,
  },
  room_ids: {
    onlyIf: ({rooms}) => rooms && rooms.length,
    serializer: ({rooms}) => rooms.map(room => room.id),
  },
  allowed: {
    onlyIf: ({allowed}) => !!allowed,
    serializer: ({allowed}) => allowed,
  },
  reason: {
    onlyIf: ({reason}) => !!reason,
    serializer: ({reason}) => reason,
  },
  start_date: {
    onlyIf: ({dates}) => dates && dates.startDate,
    serializer: filterDTHandler('start'),
  },
  end_date: {
    onlyIf: ({dates}) => dates && dates.endDate,
    serializer: filterDTHandler('end'),
  },
};
