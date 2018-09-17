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

import {requestReducer} from 'indico/utils/redux';
import {roomsReducerFactory} from '../../reducers/roomBooking/roomList';
import filterReducerFactory, {initialRoomFilterStateFactory} from '../../reducers/roomBooking/filters';
import {mapReducerFactory} from '../../reducers/roomBooking/map';
import * as actions from './actions';
import * as globalActions from '../../actions';


export const initialTimelineState = {
    isFetching: false,
    availability: [],
    dateRange: [],
    isVisible: false
};

const baseTimelineReducer = (requestAction, successAction, errorAction) => (state = initialTimelineState, action) => {
    switch (action.type) {
        case requestAction:
            return {...state, isFetching: true};
        case errorAction:
            return {...state, isFetching: false};
        case successAction:
            return {
                ...state,
                isFetching: false,
                availability: action.data.availability,
                dateRange: action.data.date_range
            };
    }
    return state;
};

function timelineReducer(state = {...initialTimelineState, isVisible: false}, action) {
    const reducer = baseTimelineReducer(
        actions.FETCH_TIMELINE_DATA_STARTED,
        actions.UPDATE_TIMELINE_DATA,
        actions.FETCH_TIMELINE_DATA_FAILED
    );
    state = reducer(state, action);

    switch (action.type) {
        case actions.TOGGLE_TIMELINE_VIEW:
            return {...state, isVisible: action.isVisible};
        case globalActions.RESET_PAGE_STATE:
            return action.namespace === 'bookRoom' ? {...state, isVisible: false} : state;
    }
    return state;
}

const unavailableReducer = baseTimelineReducer(
    actions.FETCH_UNAVAILABLE_ROOMS_STARTED,
    actions.UPDATE_UNAVAILABLE_ROOMS,
    actions.FETCH_UNAVAILABLE_ROOMS_FAILED
);

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

const bookingFormReducer = combineReducers({
    requests: combineReducers({
        booking: requestReducer(
            actions.CREATE_BOOKING_REQUEST,
            actions.CREATE_BOOKING_SUCCESS,
            actions.CREATE_BOOKING_FAILED
        ),
        timeline: requestReducer(
            actions.GET_BOOKING_AVAILABILITY_REQUEST,
            actions.GET_BOOKING_AVAILABILITY_SUCCESS,
            actions.GET_BOOKING_AVAILABILITY_ERROR
        ),
    }),
    availability: (state = null, action) => {
        switch (action.type) {
            case actions.RESET_BOOKING_AVAILABILITY:
                return null;
            case actions.SET_BOOKING_AVAILABILITY: {
                return {...action.data};
            }
            default:
                return state;
        }
    }
});

export default combineReducers({
    rooms: roomsReducerFactory('bookRoom'),
    filters: filterReducerFactory('bookRoom', initialRoomFilterStateFactory),
    map: mapReducerFactory('bookRoom'),
    timeline: timelineReducer,
    unavailableRooms: unavailableReducer,
    suggestions: suggestionsReducer,
    bookingForm: bookingFormReducer
});
