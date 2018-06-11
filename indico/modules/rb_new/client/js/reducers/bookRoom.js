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

import {roomsReducerFactory} from './roomBooking/roomList';
import filterReducerFactory from './roomBooking/filters';
import {mapReducerFactory} from './roomBooking/map';
import * as actions from '../actions';


const initialTimelineState = {
    isFetching: false,
    availability: {},
    dateRange: []
};

function timelineReducer(state = initialTimelineState, action) {
    switch (action.type) {
        case actions.FETCH_TIMELINE_DATA_STARTED:
            return {...state, isFetching: true};
        case actions.FETCH_TIMELINE_DATA_FAILED:
            return {...state, isFetching: false};
        case actions.UPDATE_TIMELINE_DATA:
            return {
                ...state,
                isFetching: false,
                availability: action.timeline.availability,
                dateRange: action.timeline.date_range
            };
        default:
            return state;
    }
}

const initialSuggestionsState = {
    isFetching: false,
    list: []
};

function suggestionsReducer(state = initialSuggestionsState, action) {
    switch (action.type) {
        case actions.FETCH_SUGGESTIONS_STARTED:
            return {...state, isFetching: true};
        case actions.FETCH_SUGGESTIONS_FAILED:
            return {...state, isFetching: false};
        case actions.UPDATE_SUGGESTIONS:
            return {...state, isFetching: false, list: action.suggestions};
        default:
            return state;
    }
}


const reducer = combineReducers({
    rooms: roomsReducerFactory('bookRoom'),
    filters: filterReducerFactory('bookRoom'),
    map: mapReducerFactory('bookRoom'),
    timeline: timelineReducer,
    suggestions: suggestionsReducer
});

export default reducer;
