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
