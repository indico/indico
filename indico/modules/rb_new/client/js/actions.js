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

import buildFetchRoomsURL from 'indico-url:rooms_new.available_rooms';
import fetchMapDetailsURL from 'indico-url:rooms_new.room_details';
import fetchMapRoomsURL from 'indico-url:rooms_new.map_rooms';
import fetchMapAspectsURL from 'indico-url:rooms_new.default_aspects';
import fetchBuildingsURL from 'indico-url:rooms_new.buildings';
import favoriteRoomsURL from 'indico-url:rooms_new.favorite_rooms';
import fetchUserInfoURL from 'indico-url:rooms_new.user_info';
import equipmentTypesURL from 'indico-url:rooms_new.equipment_types';
import fetchTimelineDataURL from 'indico-url:rooms_new.timeline';
import createBookingURL from 'indico-url:rooms_new.create_booking';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {preProcessParameters} from './util';
import {ajax as ajaxFilterRules} from './serializers/filters';
import {ajax as ajaxBookingRules} from './serializers/bookings';


// User
export const SET_FAVORITE_ROOMS = 'SET_FAVORITE_ROOMS';
export const ADD_FAVORITE_ROOM = 'ADD_FAVORITE_ROOM';
export const DEL_FAVORITE_ROOM = 'DEL_FAVORITE_ROOM';
export const SET_USER_INFO = 'SET_USER_INFO';
// Filter
export const SET_FILTER_PARAMETER = 'SET_FILTER_PARAMETER';
// Rooms
export const FETCH_ROOMS_STARTED = 'FETCH_ROOMS_STARTED';
export const FETCH_ROOMS_FAILED = 'FETCH_ROOMS_FAILED';
export const UPDATE_ROOMS = 'UPDATE_ROOMS';
export const FETCH_MAP_ROOMS_STARTED = 'FETCH_MAP_ROOMS_STARTED';
export const FETCH_MAP_ROOMS_FAILED = 'FETCH_MAP_ROOMS_FAILED';
export const UPDATE_MAP_ROOMS = 'UPDATE_MAP_ROOMS';
export const FETCH_ROOM_DETAILS_STARTED = 'FETCH_ROOM_DETAILS_STARTED';
export const FETCH_ROOM_DETAILS_FAILED = 'FETCH_ROOM_DETAILS_FAILED';
export const UPDATE_ROOM_DETAILS = 'UPDATE_ROOM_DETAILS';
export const SET_ROOM_DETAILS_MODAL = 'SET_ROOM_DETAILS_MODAL';
// Equipment types
export const SET_EQUIPMENT_TYPES = 'SET_EQUIPMENT_TYPES';
// Map
export const FETCH_MAP_ASPECTS_STARTED = 'FETCH_MAP_ASPECTS_STARTED';
export const FETCH_MAP_ASPECTS_FAILED = 'FETCH_MAP_ASPECTS_FAILED';
export const UPDATE_ASPECTS = 'UPDATE_ASPECTS';
export const UPDATE_LOCATION = 'UPDATE_LOCATION';
export const TOGGLE_MAP_SEARCH = 'TOGGLE_MAP_SEARCH';
// Buildings
export const FETCH_BUILDINGS_STARTED = 'FETCH_BUILDINGS_STARTED';
export const FETCH_BUILDINGS_FAILED = 'FETCH_BUILDINGS_FAILED';
export const FETCH_BUILDINGS = 'FETCH_BUILDINGS';
export const UPDATE_BUILDINGS = 'UPDATE_BUILDINGS';
// Timeline
export const FETCH_TIMELINE_DATA_STARTED = 'FETCH_TIMELINE_DATA_STARTED';
export const FETCH_TIMELINE_DATA_FAILED = 'FETCH_TIMELINE_DATA_FAILED';
export const UPDATE_TIMELINE_DATA = 'UPDATE_TIMELINE_DATA';
// Bookings
export const BOOKING_ONGOING = 'BOOKING_ONGOING';
export const BOOKING_CONFIRMED = 'BOOKING_CONFIRMED';
export const BOOKING_FAILED = 'BOOKING_FAILED';
export const RESET_BOOKING_STATE = 'RESET_BOOKING_STATE';

export const OPEN_FILTER_DROPDOWN = 'OPEN_FILTER_DROPDOWN';
export const CLOSE_FILTER_DROPDOWN = 'CLOSE_FILTER_DROPDOWN';

export function fetchEquipmentTypes() {
    return async (dispatch) => {
        let response;
        try {
            response = await indicoAxios.get(equipmentTypesURL());
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        if (response) {
            dispatch({type: SET_EQUIPMENT_TYPES, types: response.data});
        }
    };
}

async function _sendFavoriteRoomsRequest(method, id = null) {
    let response;
    try {
        response = await indicoAxios.request({
            method,
            url: favoriteRoomsURL(id !== null ? {room_id: id} : {})
        });
    } catch (error) {
        handleAxiosError(error);
        return;
    }
    return response;
}

export function fetchFavoriteRooms() {
    return async (dispatch) => {
        const response = await _sendFavoriteRoomsRequest('GET');
        if (response) {
            dispatch({type: SET_FAVORITE_ROOMS, rooms: response.data});
        }
    };
}

export function addFavoriteRoom(id) {
    return async (dispatch) => {
        dispatch({type: ADD_FAVORITE_ROOM, id});
        const response = await _sendFavoriteRoomsRequest('PUT', id);
        if (!response) {
            dispatch({type: DEL_FAVORITE_ROOM, id});
        }
    };
}

export function delFavoriteRoom(id) {
    return async (dispatch) => {
        dispatch({type: DEL_FAVORITE_ROOM, id});
        const response = await _sendFavoriteRoomsRequest('DELETE', id);
        if (!response) {
            dispatch({type: ADD_FAVORITE_ROOM, id});
        }
    };
}

export function fetchUserInfo() {
    return async (dispatch) => {
        let response;
        try {
            response = await indicoAxios.get(fetchUserInfoURL());
        } catch (error) {
            handleAxiosError(error);
            return;
        }

        if (response) {
            dispatch({type: SET_USER_INFO, data: response.data});
        }
    };
}

export function fetchRoomsStarted(namespace) {
    return {type: FETCH_ROOMS_STARTED, namespace};
}

export function fetchRoomsFailed(namespace) {
    return {type: FETCH_ROOMS_FAILED, namespace};
}

export function updateRooms(namespace, rooms, total, clear) {
    return {type: UPDATE_ROOMS, namespace, rooms, total, clear};
}

export function fetchRooms(namespace, clear = true) {
    return async (dispatch, getStore) => {
        const {filters, rooms: {list: oldRoomList}} = getStore()[namespace];

        dispatch(fetchRoomsStarted(namespace));

        const params = preProcessParameters(filters, ajaxFilterRules);

        Object.assign(params, {
            offset: (clear ? 0 : oldRoomList.length),
            limit: 20
        });

        let response;
        try {
            response = await indicoAxios.get(buildFetchRoomsURL(), {params});
        } catch (error) {
            handleAxiosError(error);
            dispatch(fetchRoomsFailed(namespace));
            return;
        }
        const {rooms, total} = response.data;
        dispatch(updateRooms(namespace, rooms, total, clear));
        if (namespace === 'bookRoom') {
            dispatch(fetchTimelineData());
        }
    };
}

export function fetchMapRoomsStarted(namespace) {
    return {type: FETCH_MAP_ROOMS_STARTED, namespace};
}

export function fetchMapRoomsFailed(namespace) {
    return {type: FETCH_MAP_ROOMS_FAILED, namespace};
}

export function updateMapRooms(namespace, rooms) {
    return {type: UPDATE_MAP_ROOMS, namespace, rooms};
}

export function fetchMapRooms(namespace) {
    return async (dispatch, getStore) => {
        const {filters} = getStore()[namespace];

        dispatch(fetchMapRoomsStarted(namespace));

        const params = preProcessParameters(filters, ajaxFilterRules);

        let response;
        try {
            response = await indicoAxios.get(fetchMapRoomsURL(), {params});
        } catch (error) {
            handleAxiosError(error);
            dispatch(fetchMapRoomsFailed(namespace));
            return;
        }
        const rooms = response.data.map((room) => (
            {id: room.id, name: room.full_name, lat: parseFloat(room.latitude), lng: parseFloat(room.longitude)}
        ));
        dispatch(updateMapRooms(namespace, rooms));
    };
}

export function fetchRoomDetailsStarted() {
    return {type: FETCH_ROOM_DETAILS_STARTED};
}

export function fetchRoomDetailsFailed() {
    return {type: FETCH_ROOM_DETAILS_FAILED};
}

export function updateRoomDetails(room) {
    return {type: UPDATE_ROOM_DETAILS, room};
}

export function fetchRoomDetails(id) {
    return async (dispatch, getStore) => {
        const {roomDetails: {rooms}} = getStore();
        if (id in rooms) {
            return;
        }
        dispatch(fetchRoomDetailsStarted());

        let response;
        try {
            response = await indicoAxios.get(fetchMapDetailsURL({room_id: id}));
        } catch (error) {
            handleAxiosError(error);
            dispatch(fetchRoomDetailsFailed());
            return;
        }
        dispatch(updateRoomDetails(response.data));
    };
}

export function setRoomDetailsModal(id) {
    return {type: SET_ROOM_DETAILS_MODAL, id};
}

export function setFilterParameter(namespace, param, data) {
    return {type: SET_FILTER_PARAMETER, namespace, param, data};
}

export function updateLocation(namespace, location) {
    return {type: UPDATE_LOCATION, location, namespace};
}

export function fetchMapAspectsStarted() {
    return {type: FETCH_MAP_ASPECTS_STARTED};
}

export function fetchMapAspectsFailed() {
    return {type: FETCH_MAP_ASPECTS_FAILED};
}

export function updateMapAspects(aspects) {
    return {type: UPDATE_ASPECTS, aspects};
}

export function fetchMapAspects() {
    return async (dispatch) => {
        dispatch(fetchMapAspectsStarted());

        let response;
        try {
            response = await indicoAxios.get(fetchMapAspectsURL());
        } catch (error) {
            handleAxiosError(error);
            dispatch(fetchMapAspectsFailed());
            return;
        }

        dispatch(updateMapAspects(response.data));
    };
}

export function toggleMapSearch(namespace, search) {
    return {type: TOGGLE_MAP_SEARCH, search, namespace};
}

export function fetchBuildingsStarted() {
    return {type: FETCH_BUILDINGS_STARTED};
}

export function fetchBuildingsFailed() {
    return {type: FETCH_BUILDINGS_FAILED};
}

export function updateBuildings(buildings) {
    return {type: UPDATE_BUILDINGS, buildings};
}

export function fetchBuildings() {
    return async (dispatch) => {
        dispatch(fetchBuildingsStarted());

        let response;
        try {
            response = await indicoAxios.get(fetchBuildingsURL());
        } catch (error) {
            dispatch(fetchBuildingsFailed());
            handleAxiosError(error);
            return;
        }

        dispatch(updateBuildings(response.data));
    };
}

export function fetchTimelineDataStarted() {
    return {type: FETCH_TIMELINE_DATA_STARTED};
}

export function fetchTimelineDataFailed() {
    return {type: FETCH_TIMELINE_DATA_FAILED};
}

export function updateTimelineData(timeline) {
    return {type: UPDATE_TIMELINE_DATA, timeline};
}

export function fetchTimelineData() {
    return async (dispatch, getStore) => {
        dispatch(fetchTimelineDataStarted());

        const {bookRoom: {filters, rooms: {list}}} = getStore();

        if (!list.length) {
            dispatch(updateTimelineData({date_range: [], availability: {}}));
            return;
        }

        const params = preProcessParameters(filters, ajaxFilterRules);
        params.room_ids = list.map((room) => room.id);

        let response;
        try {
            response = await indicoAxios.get(fetchTimelineDataURL(), {params});
        } catch (error) {
            dispatch(fetchTimelineDataFailed());
            handleAxiosError(error);
            return;
        }

        dispatch(updateTimelineData(response.data));
    };
}

export function createBooking(args) {
    return async (dispatch) => {
        let response;
        const params = preProcessParameters(args, ajaxBookingRules);
        dispatch({type: BOOKING_ONGOING});

        try {
            response = await indicoAxios.post(createBookingURL(), params);
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        const {success, msg, is_prebooking: isPrebooking} = response.data;
        if (success) {
            dispatch({type: BOOKING_CONFIRMED, isPrebooking});
            // reload rooms without the newly booked one
            dispatch(fetchRooms('bookRoom'));
        } else {
            dispatch({type: BOOKING_FAILED, message: msg});
        }
    };
}

export function resetBookingState() {
    return {type: RESET_BOOKING_STATE};
}

export function openFilterDropdown(name) {
    return {type: OPEN_FILTER_DROPDOWN, name};
}

export function closeFilterDropdown(name) {
    return {type: CLOSE_FILTER_DROPDOWN, name};
}
