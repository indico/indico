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

import moment from 'moment';
import {combineReducers} from 'redux';

import camelizeKeys from 'indico/utils/camelize';
import {serializeDate} from 'indico/utils/date';
import {requestReducer} from 'indico/utils/redux';
import {actions as bookRoomActions} from '../../modules/bookRoom';
import * as actions from '../../actions';
import * as calendarActions from './actions';
import * as bookingActions from '../../common/bookings/actions';
import {filterReducerFactory} from '../../common/filters';
import {processRoomFilters} from '../../common/roomSearch/reducers';
import {initialDatePickerState} from '../../common/timeline/reducers';


const datePickerState = () => ({...initialDatePickerState, selectedDate: serializeDate(moment())});

const datePickerReducer = (state = datePickerState(), action) => {
    switch (action.type) {
        case calendarActions.SET_DATE:
            return {
                ...state,
                dateRange: [],
                selectedDate: action.date
            };
        case calendarActions.SET_MODE:
            return {
                ...state,
                mode: action.mode
            };
        case actions.RESET_PAGE_STATE:
            return datePickerState();
    }
    return state;
};

export const initialDataState = {
    rows: [],
    roomIds: null
};

export const initialFilterState = {
    text: null,
    building: null,
    onlyFavorites: false
};

export const initialState = () => ({
    filters: initialFilterState,
    data: initialDataState,
    datePicker: datePickerState()
});

function filterDeletedBooking(calendar, bookingId, roomId) {
    return calendar.map((row) => {
        if (row.roomId !== roomId) {
            return row;
        }

        const newRow = {...row};
        for (const type of Object.keys(row)) {
            const bookingData = row[type];
            for (const dt of Object.keys(bookingData)) {
                const dayBookingData = bookingData[dt];
                newRow[type][dt] = dayBookingData.filter((data) => {
                    return data.reservation.id !== bookingId;
                });
            }
        }

        return newRow;
    });
}

function acceptPrebooking(calendar, bookingId, roomId) {
    return calendar.map((row) => {
        if (row.roomId !== roomId) {
            return row;
        }

        const newRow = {...row};
        const preBookings = row['preBookings'];
        for (const dt of Object.keys(preBookings)) {
            const preBookingsData = preBookings[dt];
            const preBooking = preBookingsData.find((item) => {
                return item.reservation.id === bookingId;
            });

            if (!(dt in newRow['bookings'])) {
                newRow['bookings'][dt] = [];
            }

            newRow['bookings'][dt] = [...newRow['bookings'][dt], preBooking];
            newRow['preBookings'][dt] = preBookingsData.filter((item) => {
                return item.reservation.id !== bookingId;
            });
        }

        return newRow;
    });
}

export default combineReducers({
    request: requestReducer(calendarActions.FETCH_REQUEST, calendarActions.FETCH_SUCCESS, calendarActions.FETCH_ERROR),
    filters: filterReducerFactory('calendar', initialFilterState, processRoomFilters),
    data: (state = initialDataState, action) => {
        switch (action.type) {
            case calendarActions.ROWS_RECEIVED:
                return {...state, rows: camelizeKeys(action.data)};
            case calendarActions.ROOM_IDS_RECEIVED:
                return {...state, roomIds: action.data.slice()};
            case bookingActions.BOOKING_DELETE_SUCCESS: {
                const {bookingId, roomId} = camelizeKeys(action.data);
                const {rows} = state;
                return {...state, rows: filterDeletedBooking(rows, bookingId, roomId)};
            }
            case bookingActions.BOOKING_STATE_UPDATED: {
                const {booking: {id, roomId}, bookingState} = camelizeKeys(action.data);
                const {rows} = state;
                let newRows;

                if (['rejected', 'cancelled'].indexOf(bookingState) !== -1) {
                    newRows = filterDeletedBooking(rows, id, roomId);
                } else if (bookingState === 'approved') {
                    newRows = acceptPrebooking(rows, id, roomId);
                }

                return {...state, rows: newRows};
            }
            case bookRoomActions.CREATE_BOOKING_SUCCESS: {
                const bookingData = camelizeKeys(action.data);
                const {roomId} = bookingData;
                const {rows} = state;
                const newRows = rows.map((row) => {
                    if (row.roomId !== roomId) {
                        return row;
                    }

                    const newRow = {...row};
                    for (const type of ['bookings', 'preBookings']) {
                        if (!(type in bookingData)) {
                            continue;
                        }

                        const values = bookingData[type];
                        for (const dt of Object.keys(values)) {
                            const previousValues = newRow[type][dt] || [];
                            newRow[type][dt] = [...previousValues, ...values[dt]];
                        }
                    }
                    return newRow;
                });

                return {...state, rows: newRows};
            }
            default:
                return state;
        }
    },
    datePicker: datePickerReducer
});
