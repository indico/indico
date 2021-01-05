// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {combineReducers} from 'redux';

import {camelizeKeys} from 'indico/utils/case';
import {requestReducer} from 'indico/utils/redux';

import * as bookingsActions from './actions';

export default combineReducers({
  requests: combineReducers({
    details: requestReducer(
      bookingsActions.FETCH_BOOKING_DETAILS_REQUEST,
      bookingsActions.FETCH_BOOKING_DETAILS_SUCCESS,
      bookingsActions.FETCH_BOOKING_DETAILS_ERROR
    ),
    changePrebookingState: requestReducer(
      bookingsActions.BOOKING_STATE_CHANGE_REQUEST,
      bookingsActions.BOOKING_STATE_CHANGE_SUCCESS,
      bookingsActions.BOOKING_STATE_CHANGE_ERROR
    ),
  }),
  details: (state = {}, action) => {
    switch (action.type) {
      case bookingsActions.BOOKING_DETAILS_RECEIVED: {
        const data = camelizeKeys(action.data);
        return {...state, [data.id]: data};
      }
      case bookingsActions.BOOKING_STATE_UPDATED: {
        const data = camelizeKeys(action.data.booking);
        return {...state, [data.id]: {...state[data.id], ...data}};
      }
      case bookingsActions.DELETE_BOOKING_SUCCESS: {
        const {bookingId} = camelizeKeys(action.data);
        const newState = {...state};
        delete newState[bookingId];
        return {...newState};
      }
      case bookingsActions.UPDATED_BOOKING_RECEIVED: {
        const {booking} = camelizeKeys(action.data);
        return {...state, [booking.id]: booking};
      }
      default:
        return state;
    }
  },
});
