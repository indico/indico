// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {combineReducers} from 'redux';

import {camelizeKeys} from 'indico/utils/case';
import {requestReducer} from 'indico/utils/redux';
import * as roomsActions from './actions';
import * as bookingActions from '../bookings/actions';
import * as bookRoomActions from '../../modules/bookRoom/actions';

function filterAvailability(roomAvailability, bookingId) {
  return roomAvailability.map(availability => {
    const bookings = availability.bookings || [];
    const newBookings = bookings.filter(booking => {
      return booking.reservation.id !== bookingId;
    });
    return {...availability, bookings: newBookings};
  });
}

export default combineReducers({
  requests: combineReducers({
    // global data
    equipmentTypes: requestReducer(
      roomsActions.FETCH_EQUIPMENT_TYPES_REQUEST,
      roomsActions.FETCH_EQUIPMENT_TYPES_SUCCESS,
      roomsActions.FETCH_EQUIPMENT_TYPES_ERROR
    ),
    // room-specific data
    rooms: requestReducer(
      roomsActions.FETCH_ROOMS_REQUEST,
      roomsActions.FETCH_ROOMS_SUCCESS,
      roomsActions.FETCH_ROOMS_ERROR
    ),
    availability: requestReducer(
      roomsActions.FETCH_AVAILABILITY_REQUEST,
      roomsActions.FETCH_AVAILABILITY_SUCCESS,
      roomsActions.FETCH_AVAILABILITY_ERROR
    ),
    attributes: requestReducer(
      roomsActions.FETCH_ATTRIBUTES_REQUEST,
      roomsActions.FETCH_ATTRIBUTES_SUCCESS,
      roomsActions.FETCH_ATTRIBUTES_ERROR
    ),
  }),
  equipmentTypes: (state = [], action) => {
    switch (action.type) {
      case roomsActions.EQUIPMENT_TYPES_RECEIVED:
        return camelizeKeys(action.data);
      default:
        return state;
    }
  },
  rooms: (state = [], action) => {
    switch (action.type) {
      case roomsActions.ROOMS_RECEIVED:
        return camelizeKeys(action.data);
      case roomsActions.ROOM_DETAILS_RECEIVED:
        return [...state.filter(room => room.id !== action.data.id), camelizeKeys(action.data)];
      default:
        return state;
    }
  },
  availability: (state = {}, action) => {
    switch (action.type) {
      case roomsActions.AVAILABILITY_RECEIVED: {
        const {id, availability} = action.data;
        return {...state, [id]: availability};
      }
      case bookRoomActions.CREATE_BOOKING_SUCCESS: {
        const {
          calendarData: {bookings},
          roomId,
        } = camelizeKeys(action.data);
        if (!bookings) {
          return state;
        }

        const {[roomId]: roomAvailability} = state;
        const av = roomAvailability.map(roomAv => {
          if (!(roomAv.day in bookings)) {
            return roomAv;
          }

          const oldBookings = roomAv.bookings || [];
          return {...roomAv, bookings: [...oldBookings, ...bookings[roomAv.day]]};
        });

        return {...state, [roomId]: av};
      }
      case bookingActions.BOOKING_STATE_UPDATED: {
        const {
          booking: {id, roomId, state: bookingState},
        } = camelizeKeys(action.data);
        if (bookingState === 'rejected' || bookingState === 'cancelled') {
          const {[roomId]: roomAvailability} = state;
          if (!roomAvailability) {
            return state;
          }
          return {...state, [roomId]: filterAvailability(roomAvailability, id)};
        }

        return state;
      }
      case bookingActions.DELETE_BOOKING_SUCCESS: {
        const {roomId, bookingId} = camelizeKeys(action.data);
        const {[roomId]: roomAvailability} = state;
        if (!roomAvailability) {
          return state;
        }
        return {...state, [roomId]: filterAvailability(roomAvailability, bookingId)};
      }
      default:
        return state;
    }
  },
  attributes: (state = {}, action) => {
    switch (action.type) {
      case roomsActions.ATTRIBUTES_RECEIVED: {
        const {id, attributes} = action.data;
        return {...state, [id]: attributes};
      }
      default:
        return state;
    }
  },
});
