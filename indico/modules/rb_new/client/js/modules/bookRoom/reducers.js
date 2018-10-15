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
import * as actions from './actions';
import * as globalActions from '../../actions';
import {roomSearchReducerFactory} from '../../common/roomSearch';


export const initialTimelineState = {
    availability: [],
    dateRange: [],
    isVisible: false,
    roomIds: [],
    params: null,
};

const timelineReducer = combineReducers({
    request: requestReducer(
        actions.GET_TIMELINE_REQUEST,
        actions.GET_TIMELINE_SUCCESS,
        actions.GET_TIMELINE_ERROR
    ),
    data: (state = initialTimelineState, action) => {
        switch (action.type) {
            case actions.TOGGLE_TIMELINE_VIEW:
                return {...state, isVisible: action.visible};
            case globalActions.RESET_PAGE_STATE:
                return action.namespace === 'bookRoom' ? {...state, isVisible: false} : state;
            case actions.INIT_TIMELINE:
                return {
                    ...state,
                    dateRange: [],
                    availability: [],
                    params: action.params,
                    roomIds: action.roomIds
                };
            case actions.ADD_TIMELINE_ROOMS:
                return {
                    ...state,
                    roomIds: state.roomIds.concat(action.roomIds),
                };
            case actions.TIMELINE_RECEIVED:
                return {
                    ...state,
                    dateRange: action.data.date_range,
                    availability: state.availability.concat(action.data.availability),
                };
            case actions.CREATE_BOOKING_SUCCESS: {
                const {data: {room_id: roomId}} = action;
                const {roomIds, availability} = state;
                return {
                    ...state,
                    roomIds: roomIds.filter((id) => id !== roomId),
                    availability: availability.filter(([id]) => id !== roomId)
                };
            }
            default:
                return state;
        }
    }
});


const unavailableReducer = combineReducers({
    request: requestReducer(
        actions.GET_UNAVAILABLE_TIMELINE_REQUEST,
        actions.GET_UNAVAILABLE_TIMELINE_SUCCESS,
        actions.GET_UNAVAILABLE_TIMELINE_ERROR
    ),
    data: (state = [], action) => {
        switch (action.type) {
            case actions.GET_UNAVAILABLE_TIMELINE_REQUEST:
                return [];
            case actions.UNAVAILABLE_TIMELINE_RECEIVED:
                return action.data.availability;
            default:
                return state;
        }
    }
});

const suggestionsReducer = combineReducers({
    request: requestReducer(
        actions.FETCH_SUGGESTIONS_REQUEST,
        actions.FETCH_SUGGESTIONS_SUCCESS,
        actions.FETCH_SUGGESTIONS_ERROR
    ),
    data: (state = [], action) => {
        switch (action.type) {
            case actions.RESET_SUGGESTIONS:
                return [];
            case actions.SUGGESTIONS_RECEIVED:
                return action.data;
            default:
                return state;
        }
    }
});

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
            case actions.SET_BOOKING_AVAILABILITY:
                return {...action.data.availability, dateRange: action.data.date_range};
            default:
                return state;
        }
    }
});

export default roomSearchReducerFactory('bookRoom', {
    timeline: timelineReducer,
    unavailableRooms: unavailableReducer,
    suggestions: suggestionsReducer,
    bookingForm: bookingFormReducer
});
