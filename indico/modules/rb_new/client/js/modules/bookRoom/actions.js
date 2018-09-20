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
import fetchTimelineURL from 'indico-url:rooms_new.timeline';
import fetchSuggestionsURL from 'indico-url:rooms_new.suggestions';
import searchRoomsURL from 'indico-url:rooms_new.search_rooms';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {ajaxAction, submitFormAction} from 'indico/utils/redux';
import {ajax as ajaxRules} from './serializers';
import {ajax as ajaxFilterRules} from '../../serializers/filters';
import {preProcessParameters} from '../../util';

import {roomSearchActionsFactory} from '../../common/roomSearch';


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
export const TOGGLE_TIMELINE_VIEW = 'bookRoom/TOGGLE_TIMELINE_VIEW';
export const INIT_TIMELINE = 'bookRoom/INIT_TIMELINE';
export const ADD_TIMELINE_ROOMS = 'bookRoom/ADD_TIMELINE_ROOMS';
export const GET_TIMELINE_REQUEST = 'bookRoom/GET_TIMELINE_REQUEST';
export const GET_TIMELINE_SUCCESS = 'bookRoom/GET_TIMELINE_SUCCESS';
export const GET_TIMELINE_ERROR = 'bookRoom/GET_TIMELINE_ERROR';
export const TIMELINE_RECEIVED = 'bookRoom/TIMELINE_RECEIVED';

// Unavailable room list
export const GET_UNAVAILABLE_TIMELINE_REQUEST = 'bookRoom/GET_UNAVAILABLE_TIMELINE_REQUEST';
export const GET_UNAVAILABLE_TIMELINE_SUCCESS = 'bookRoom/GET_UNAVAILABLE_TIMELINE_SUCCESS';
export const GET_UNAVAILABLE_TIMELINE_ERROR = 'bookRoom/GET_UNAVAILABLE_TIMELINE_ERROR';
export const UNAVAILABLE_TIMELINE_RECEIVED = 'bookRoom/UNAVAILABLE_TIMELINE_RECEIVED';

// Suggestions
export const FETCH_SUGGESTIONS_STARTED = 'bookRoom/FETCH_SUGGESTIONS_STARTED';
export const FETCH_SUGGESTIONS_FAILED = 'bookRoom/FETCH_SUGGESTIONS_FAILED';
export const UPDATE_SUGGESTIONS = 'bookRoom/UPDATE_SUGGESTIONS';
export const RESET_SUGGESTIONS = 'bookRoom/RESET_SUGGESTIONS';


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
    const {dates, timeSlot, recurrence} = filters;
    const params = preProcessParameters({dates, timeSlot, recurrence}, ajaxFilterRules);
    return ajaxAction(
        () => indicoAxios.get(fetchTimelineURL({room_id: room.id}), {params}),
        GET_BOOKING_AVAILABILITY_REQUEST,
        [SET_BOOKING_AVAILABILITY, GET_BOOKING_AVAILABILITY_SUCCESS],
        GET_BOOKING_AVAILABILITY_ERROR
    );
}

export function fetchUnavailableRooms(filters) {
    return async (dispatch) => {
        dispatch({type: GET_UNAVAILABLE_TIMELINE_REQUEST});

        const searchParams = preProcessParameters(filters, ajaxFilterRules);
        searchParams.unavailable = true;
        let response;
        try {
            response = await indicoAxios.get(searchRoomsURL(), {params: searchParams});
        } catch (error) {
            const message = handleAxiosError(error, true);
            dispatch({type: GET_UNAVAILABLE_TIMELINE_ERROR, error: message});
            return;
        }

        const roomIds = response.data.rooms;
        const {dates, timeSlot, recurrence} = filters;
        const timelineParams = preProcessParameters({dates, timeSlot, recurrence}, ajaxFilterRules);
        return await ajaxAction(
            () => indicoAxios.post(fetchTimelineURL(), {room_ids: roomIds}, {params: timelineParams}),
            null,
            [UNAVAILABLE_TIMELINE_RECEIVED, GET_UNAVAILABLE_TIMELINE_SUCCESS],
            GET_UNAVAILABLE_TIMELINE_ERROR
        )(dispatch);
    };
}

export function initTimeline(roomIds, dates, timeSlot, recurrence) {
    return {
        type: INIT_TIMELINE,
        params: {dates, timeSlot, recurrence},
        roomIds
    };
}

export function addTimelineRooms(roomIds) {
    return {
        type: ADD_TIMELINE_ROOMS,
        roomIds
    };
}

export function fetchTimeline() {
    const PER_PAGE = 20;

    return async (dispatch, getStore) => {
        const {
            bookRoom: {
                timeline: {
                    data: {
                        params: stateParams,
                        roomIds: stateRoomIds,
                        availability: stateAvailability,
                    }
                }
            }
        } = getStore();
        const params = preProcessParameters(stateParams, ajaxFilterRules);
        const numFetchedIds = stateAvailability.length;
        const roomIds = stateRoomIds.slice(numFetchedIds, numFetchedIds + PER_PAGE);
        if (!roomIds.length) {
            console.warn('Tried to fetch timeline for zero rooms');
            return Promise.reject();
        }

        return await ajaxAction(
            () => indicoAxios.post(fetchTimelineURL(), {room_ids: roomIds}, {params}),
            GET_TIMELINE_REQUEST,
            [TIMELINE_RECEIVED, GET_TIMELINE_SUCCESS],
            GET_TIMELINE_ERROR
        )(dispatch);
    };
}

export function toggleTimelineView(visible) {
    return {type: TOGGLE_TIMELINE_VIEW, visible};
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
    };
}

export function updateRoomSuggestions(suggestions) {
    return {type: UPDATE_SUGGESTIONS, suggestions};
}

export function resetRoomSuggestions() {
    return {type: RESET_SUGGESTIONS};
}

export const {searchRooms} = roomSearchActionsFactory('bookRoom');
