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
import * as calendarActions from './actions';
import {filterReducerFactory} from '../../common/filters';
import {processRoomFilters} from '../../common/roomSearch/reducers';
import {initialDatePickerState} from '../../common/timeline/reducers';


const datePickerState = () => ({...initialDatePickerState, selectedDate: serializeDate(moment())});

const datePickerReducer = (state = datePickerState(), action) => {
    if (action.type === calendarActions.SET_DATE) {
        return {
            ...state,
            dateRange: [],
            selectedDate: action.date
        };
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

export default combineReducers({
    request: requestReducer(calendarActions.FETCH_REQUEST, calendarActions.FETCH_SUCCESS, calendarActions.FETCH_ERROR),
    filters: filterReducerFactory('calendar', initialFilterState, processRoomFilters),
    data: (state = initialDataState, action) => {
        switch (action.type) {
            case calendarActions.ROWS_RECEIVED:
                return {...state, rows: camelizeKeys(action.data)};
            case calendarActions.SET_DATE:
                return {...state, rows: []};
            case calendarActions.ROOM_IDS_RECEIVED:
                return {...state, roomIds: action.data.slice()};
            case bookRoomActions.CREATE_BOOKING_SUCCESS: {
                const {data: {occurrences, room_id: roomId}} = action;
                const {rows} = state;
                const newRows = rows.map((row) => {
                    if (row.room_id !== roomId) {
                        return row;
                    }

                    const newRow = {...row};
                    for (const dt of Object.keys(occurrences)) {
                        newRow.bookings[dt] = [...newRow.bookings[dt], ...occurrences[dt]];
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
