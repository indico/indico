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

import buildSearchRoomsURL from 'indico-url:rooms_new.search_rooms';
import fetchMapRoomsURL from 'indico-url:rooms_new.map_rooms';
import fetchMapAspectsURL from 'indico-url:rooms_new.default_aspects';
import fetchBuildingsURL from 'indico-url:rooms_new.buildings';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {preProcessParameters} from './util';
import {ajax as ajaxFilterRules} from './serializers/filters';


// Page state
export const INIT = 'INIT';
export const RESET_PAGE_STATE = 'RESET_PAGE_STATE';
// Filter
export const SET_FILTER_PARAMETER = 'SET_FILTER_PARAMETER';
export const SET_FILTERS = 'SET_FILTERS';
// Rooms
export const SEARCH_ROOMS_STARTED = 'SEARCH_ROOMS_STARTED';
export const SEARCH_ROOMS_FAILED = 'SEARCH_ROOMS_FAILED';
export const UPDATE_ROOMS = 'UPDATE_ROOMS';
export const FETCH_MAP_ROOMS_STARTED = 'FETCH_MAP_ROOMS_STARTED';
export const FETCH_MAP_ROOMS_FAILED = 'FETCH_MAP_ROOMS_FAILED';
export const UPDATE_MAP_ROOMS = 'UPDATE_MAP_ROOMS';
export const UPDATE_ROOM_DETAILS = 'UPDATE_ROOM_DETAILS';
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

const ROOM_RESULT_LIMIT = 20;


export function init() {
    return {type: INIT};
}

export function updateRooms(namespace, rooms, matching, total, loadMore) {
    return {type: UPDATE_ROOMS, namespace, rooms, matching, total, loadMore};
}

export function searchRooms(namespace, loadMore = false) {
    return async (dispatch, getStore) => {
        const {filters, rooms: {list: oldRoomList}} = getStore()[namespace];

        dispatch({type: SEARCH_ROOMS_STARTED, namespace, loadMore});

        const params = preProcessParameters(filters, ajaxFilterRules);

        Object.assign(params, {
            offset: (loadMore ? oldRoomList.length : 0),
            limit: ROOM_RESULT_LIMIT
        });

        let response;
        try {
            response = await indicoAxios.get(buildSearchRoomsURL(), {params});
        } catch (error) {
            handleAxiosError(error);
            dispatch({type: SEARCH_ROOMS_FAILED, namespace});
            return;
        }

        const {rooms, matching, total} = response.data;
        dispatch(updateRooms(namespace, rooms, matching, total, loadMore));
        return matching;
    };
}

export function updateMapRooms(namespace, rooms) {
    return {type: UPDATE_MAP_ROOMS, namespace, rooms};
}

export function fetchMapRooms(namespace) {
    return async (dispatch, getStore) => {
        const {filters} = getStore()[namespace];

        dispatch({type: FETCH_MAP_ROOMS_STARTED, namespace});

        const params = preProcessParameters(filters, ajaxFilterRules);

        let response;
        try {
            response = await indicoAxios.get(fetchMapRoomsURL(), {params});
        } catch (error) {
            handleAxiosError(error);
            dispatch({type: FETCH_MAP_ROOMS_FAILED, namespace});
            return;
        }
        const rooms = response.data.map((room) => (
            {id: room.id, name: room.full_name, lat: parseFloat(room.latitude), lng: parseFloat(room.longitude)}
        ));
        dispatch(updateMapRooms(namespace, rooms));
    };
}

export function setFilterParameter(namespace, param, data) {
    return {type: SET_FILTER_PARAMETER, namespace, param, data};
}

export function setFilters(namespace, params) {
    return {type: SET_FILTERS, namespace, params};
}

export function resetPageState(namespace) {
    return {type: RESET_PAGE_STATE, namespace};
}

export function updateLocation(namespace, location) {
    return {type: UPDATE_LOCATION, location, namespace};
}

export function fetchMapAspects() {
    return async (dispatch) => {
        dispatch({type: FETCH_MAP_ASPECTS_STARTED});

        let response;
        try {
            response = await indicoAxios.get(fetchMapAspectsURL());
        } catch (error) {
            handleAxiosError(error);
            dispatch({type: FETCH_MAP_ASPECTS_FAILED});
            return;
        }

        dispatch({type: UPDATE_ASPECTS, aspects: response.data});
    };
}

export function toggleMapSearch(namespace, search) {
    return {type: TOGGLE_MAP_SEARCH, search, namespace};
}

export function fetchBuildings() {
    return async (dispatch) => {
        dispatch({type: FETCH_BUILDINGS_STARTED});

        let response;
        try {
            response = await indicoAxios.get(fetchBuildingsURL());
        } catch (error) {
            dispatch({type: FETCH_BUILDINGS_FAILED});
            handleAxiosError(error);
            return;
        }

        dispatch({type: UPDATE_BUILDINGS, buildings: response.data});
    };
}
