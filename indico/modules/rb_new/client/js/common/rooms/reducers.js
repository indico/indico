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

import {combineReducers} from 'redux';

import camelizeKeys from 'indico/utils/camelize';
import {requestReducer} from 'indico/utils/redux';
import * as roomsActions from './actions';
import {actions as bookingActions} from '../bookings';
import {actions as bookRoomActions} from '../../modules/bookRoom';


function filterAvailability(roomAvailability, bookingId) {
    return roomAvailability.map((availability) => {
        const bookings = availability.bookings || [];
        const newBookings = bookings.filter((booking) => {
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
                return action.data.map(x => camelizeKeys(x));
            default:
                return state;
        }
    },
    rooms: (state = {}, action) => {
        switch (action.type) {
            case roomsActions.ROOMS_RECEIVED:
                return action.data;
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
                const {bookings, roomId} = camelizeKeys(action.data);
                if (!bookings) {
                    return state;
                }

                const {[roomId]: roomAvailability} = state;
                const av = roomAvailability.map((roomAv) => {
                    if (!(roomAv.day in bookings)) {
                        return roomAv;
                    }

                    const oldBookings = roomAv.bookings || [];
                    return {...roomAv, bookings: [...oldBookings, ...bookings[roomAv.day]]};
                });

                return {...state, [roomId]: av};
            }
            case bookingActions.BOOKING_STATE_UPDATED: {
                const {booking: {id, roomId}, bookingState} = camelizeKeys(action.data);
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
