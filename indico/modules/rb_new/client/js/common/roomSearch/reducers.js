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

import {filterReducerFactory} from '../filters';
import {mapSearchReducerFactory} from '../map';
import {roomSearchActionsFactory} from './actions';
import {actions as bookRoomActions} from '../../modules/bookRoom';
import {sanitizeRecurrence} from '../../util';


export function processRoomFilters(filters, param) {
    if (param === 'recurrence') {
        sanitizeRecurrence(filters);
    }

    return filters;
}


export function initialRoomFilterStateFactory(namespace) {
    const state = {
        text: null,
        building: null,
        capacity: null,
        onlyFavorites: false,
        onlyMine: false,
        equipment: [],
        features: [],
        bounds: null,
        division: null,
        error: false
    };

    if (namespace === 'bookRoom') {
        Object.assign(state, {
            recurrence: {
                type: null,
                number: null,
                interval: null
            },
            dates: {
                startDate: null,
                endDate: null
            },
            timeSlot: {
                startTime: null,
                endTime: null
            },
        });
    } else if (namespace === 'calendar') {
        Object.assign(state, {
            myBookings: false,
            hideUnused: false,
            showInactive: false,
        });
    }

    if (namespace === 'roomList' || namespace === 'calendar') {
        Object.assign(state, {
            onlyAuthorized: false,
        });
    }

    return state;
}


export function roomSearchReducerFactory(namespace, extra = {}) {
    const initialSearchResultsState = {
        rooms: [],
        roomsWithoutAvailabilityFilter: [],
        total: 0,
    };
    const actions = roomSearchActionsFactory(namespace);

    return combineReducers({
        search: combineReducers({
            request: requestReducer(
                actions.SEARCH_ROOMS_REQUEST,
                actions.SEARCH_ROOMS_SUCCESS,
                actions.SEARCH_ROOMS_ERROR
            ),
            results: (state = initialSearchResultsState, action) => {
                switch (action.type) {
                    case actions.SEARCH_RESULTS_RECEIVED:
                        return camelizeKeys(action.data);
                    case bookRoomActions.CREATE_BOOKING_SUCCESS: {
                        if (namespace !== 'bookRoom') {
                            return state;
                        }

                        const {data: {room_id: roomId}} = action;
                        const {rooms} = state;
                        return {
                            ...state,
                            rooms: rooms.filter((id) => id !== roomId)
                        };
                    }
                    default:
                        return state;
                }
            }
        }),
        filters: filterReducerFactory(namespace, initialRoomFilterStateFactory, processRoomFilters),
        map: mapSearchReducerFactory(namespace),
        ...extra
    });
}
