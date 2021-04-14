// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {combineReducers} from 'redux';

import {camelizeKeys} from 'indico/utils/case';
import {requestReducer} from 'indico/utils/redux';

import {actions as adminActions} from '../admin';

import * as landingActions from './actions';

export default combineReducers({
  stats: combineReducers({
    request: requestReducer(
      landingActions.FETCH_STATS_REQUEST,
      landingActions.FETCH_STATS_SUCCESS,
      landingActions.FETCH_STATS_ERROR
    ),
    data: (state = null, action) => {
      switch (action.type) {
        case landingActions.STATS_RECEIVED:
          return camelizeKeys(action.data);
        default:
          return state;
      }
    },
  }),
  upcomingBookings: combineReducers({
    request: requestReducer(
      landingActions.FETCH_BOOKINGS_REQUEST,
      landingActions.FETCH_BOOKINGS_SUCCESS,
      landingActions.FETCH_BOOKINGS_ERROR
    ),
    data: (state = [], action) => {
      switch (action.type) {
        case landingActions.BOOKINGS_RECEIVED:
          return camelizeKeys(action.data);
        case adminActions.ROOM_DELETED:
          return [];
        default:
          return state;
      }
    },
  }),
});
