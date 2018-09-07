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

import createBookingURL from 'indico-url:rooms_new.create_booking';
import fetchTimelineDataURL from 'indico-url:rooms_new.timeline';
import fetchSuggestionsURL from 'indico-url:rooms_new.suggestions';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {ajaxAction, submitFormAction} from 'indico/utils/redux';
import {ajax as ajaxRules} from './serializers';
import {ajax as ajaxFilterRules} from '../../serializers/filters';
import {preProcessParameters} from '../../util';

import {searchRooms as roomListSearchRooms} from '../../actions';

// Booking creation
export const CREATE_BOOKING_REQUEST = 'bookRoom/CREATE_BOOKING_REQUEST';
export const CREATE_BOOKING_SUCCESS = 'bookRoom/CREATE_BOOKING_SUCCESS';
export const CREATE_BOOKING_FAILED = 'bookRoom/CREATE_BOOKING_FAILED';

// Checking availability of room
export const GET_BOOKING_AVAILABILITY_REQUEST = 'bookRoom/GET_BOOKING_AVAILABILITY_REQUEST';
export const GET_BOOKING_AVAILABILITY_SUCCESS = 'bookRoom/GET_BOOKING_AVAILABILITY_SUCCESS';
export const GET_BOOKING_AVAILABILITY_ERROR = 'bookRoom/GET_BOOKING_AVAILABILITY_ERROR';
export const RESET_BOOKING_AVAILABILITY = 'bookRoom/RESET_BOOKING_AVAILABILITY';
export const SET_BOOKING_AVAILABILITY = 'bookRoom/SET_BOOKING_AVAILABILITY';

// Timeline
export const FETCH_TIMELINE_DATA_STARTED = 'bookRoom/FETCH_TIMELINE_DATA_STARTED';
export const FETCH_TIMELINE_DATA_FAILED = 'bookRoom/FETCH_TIMELINE_DATA_FAILED';
export const UPDATE_TIMELINE_DATA = 'bookRoom/UPDATE_TIMELINE_DATA';
export const TOGGLE_TIMELINE_VIEW = 'bookRoom/TOGGLE_TIMELINE_VIEW';

// Suggestions
export const FETCH_SUGGESTIONS_STARTED = 'bookRoom/FETCH_SUGGESTIONS_STARTED';
export const FETCH_SUGGESTIONS_FAILED = 'bookRoom/FETCH_SUGGESTIONS_FAILED';
export const UPDATE_SUGGESTIONS = 'bookRoom/UPDATE_SUGGESTIONS';


export function createBooking(args) {
    const params = preProcessParameters(args, ajaxRules);
    return submitFormAction(
        () => indicoAxios.post(createBookingURL(), params),
        CREATE_BOOKING_REQUEST, CREATE_BOOKING_SUCCESS, CREATE_BOOKING_FAILED
    );
}

export function resetBookingAvailability() {
    return {type: RESET_BOOKING_AVAILABILITY};
}

export function fetchBookingAvailability(room, filters) {
    return ajaxAction(
        () => _fetchTimelineData(filters, [room]),
        GET_BOOKING_AVAILABILITY_REQUEST,
        [SET_BOOKING_AVAILABILITY, GET_BOOKING_AVAILABILITY_SUCCESS],
        GET_BOOKING_AVAILABILITY_ERROR,
        ({availability, date_range: dateRange}) => ({...availability[room.id], dateRange})
    );
}

async function _fetchTimelineData(filters, rooms, limit = null) {
    const params = preProcessParameters(filters, ajaxFilterRules);
    params.additional_room_ids = rooms.map((room) => room.id);

    if (limit) {
        params.limit = limit;
    }

    return await indicoAxios.get(fetchTimelineDataURL(), {params});
}

export function fetchTimelineData() {
    return async (dispatch, getStore) => {
        dispatch({type: FETCH_TIMELINE_DATA_STARTED});

        const {bookRoom: {filters, suggestions: {list: suggestionsList}, rooms: {list}}} = getStore();

        if (!list.length && !suggestionsList.length) {
            dispatch({type: UPDATE_TIMELINE_DATA, timeline: {date_range: [], availability: null}});
            return;
        }
        let response;
        const rooms = suggestionsList.map(({room}) => room);
        try {
            response = await _fetchTimelineData(filters, rooms, list.length);
        } catch (error) {
            handleAxiosError(error);
            dispatch({type: FETCH_TIMELINE_DATA_FAILED});
            return;
        }
        dispatch({type: UPDATE_TIMELINE_DATA, timeline: response.data});
    };
}

export function toggleTimelineView(isVisible) {
    return {type: TOGGLE_TIMELINE_VIEW, isVisible};
}

export function fetchRoomSuggestions() {
    return async (dispatch, getStore) => {
        dispatch({type: FETCH_SUGGESTIONS_STARTED});

        let response;
        const {bookRoom: {filters}} = getStore();
        const params = preProcessParameters(filters, ajaxFilterRules);

        try {
            response = await indicoAxios.get(fetchSuggestionsURL(), {params});
        } catch (error) {
            dispatch({type: FETCH_SUGGESTIONS_FAILED});
            handleAxiosError(error);
            return;
        }

        dispatch(updateRoomSuggestions(response.data));
        dispatch(fetchTimelineData());
    };
}

export function updateRoomSuggestions(suggestions) {
    return {type: UPDATE_SUGGESTIONS, suggestions};
}

export function searchRooms(loadMore = false) {
    return async (dispatch, getStore) => {
        const total = await dispatch(roomListSearchRooms('bookRoom', loadMore));
        dispatch(updateRoomSuggestions([]));
        const {bookRoom: {rooms: {list}}} = getStore();
        if (list.length === total || total === 0) {
            dispatch(fetchRoomSuggestions());
        } else {
            dispatch(fetchTimelineData());
        }
    };
}
