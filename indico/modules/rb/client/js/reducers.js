// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {connectRouter} from 'connected-react-router';

import {reducer as configReducer} from './common/config';
import {reducer as mapReducer} from './common/map';
import {reducer as roomsReducer} from './common/rooms';
import {reducer as bookRoomReducer} from './modules/bookRoom';
import {reducer as userReducer} from './common/user';
import {reducer as blockingsReducer} from './modules/blockings';
import {reducer as calendarReducer} from './modules/calendar';
import {reducer as landingReducer} from './modules/landing';
import {reducer as roomListReducer} from './modules/roomList';
import {reducer as bookingReducer} from './common/bookings';
import {reducer as adminReducer} from './modules/admin';
import {reducer as linkingReducer} from './common/linking';

export default history => ({
  router: connectRouter(history),
  config: configReducer,
  user: userReducer,
  bookRoom: bookRoomReducer,
  roomList: roomListReducer,
  map: mapReducer,
  rooms: roomsReducer,
  blockings: blockingsReducer,
  calendar: calendarReducer,
  landing: landingReducer,
  bookings: bookingReducer,
  admin: adminReducer,
  linking: linkingReducer,
});
