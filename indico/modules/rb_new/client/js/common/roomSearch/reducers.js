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

import {filterReducerFactory} from '../filters';
import {mapReducerFactory} from '../../reducers/roomBooking/map';
import {roomSearchActionsFactory} from './actions';
import {parseSearchBarText, sanitizeRecurrence} from '../../util';


function processRoomFilters(filters, param) {
    if (param === 'recurrence') {
        sanitizeRecurrence(filters);
    } else if (param === 'text') {
        const dd = parseSearchBarText(filters.text);
        filters.text = dd.text || null;
        filters.building = dd.building || null;
        filters.floor = dd.floor || null;
    }

    return filters;
}


export function initialRoomFilterStateFactory(namespace) {
    const state = {
        text: null,
        capacity: null,
        onlyFavorites: false,
        onlyMine: false,
        equipment: [],
        bounds: null,
        building: null,
        floor: null,
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
    }

    return state;
}


export function roomSearchReducerFactory(namespace, extra = {}) {
    const initialSearchResultsState = {
        rooms: [],
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
                    default:
                        return state;
                }
            }
        }),
        filters: filterReducerFactory(namespace, initialRoomFilterStateFactory, processRoomFilters),
        map: mapReducerFactory(namespace),
        ...extra
    });
}
