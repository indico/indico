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

import buildFetchRoomsUrl from 'indico-url:rooms_new.available_rooms';
import fetchDefaultLocationUrl from 'indico-url:rooms_new.default_location';
import fetchBuildingsUrl from 'indico-url:rooms_new.buildings';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {preProcessParameters} from './util';
import {ajax as ajaxFilterRules} from './serializers/filters';


// User
export const SET_USER = 'SET_USER';
// Filter
export const SET_FILTER_PARAMETER = 'SET_FILTER_PARAMETER';
// Rooms
export const FETCH_ROOMS_STARTED = 'FETCH_ROOMS_STARTED';
export const FETCH_ROOMS_FAILED = 'FETCH_ROOMS_FAILED';
export const UPDATE_ROOMS = 'UPDATE_ROOMS';
// Map
export const FETCH_DEFAULT_LOCATION_STARTED = 'FETCH_DEFAULT_LOCATION_STARTED';
export const FETCH_DEFAULT_LOCATION_FAILED = 'FETCH_DEFAULT_LOCATION_FAILED';
export const UPDATE_LOCATION = 'UPDATE_LOCATION';
export const TOGGLE_MAP_SEARCH = 'TOGGLE_MAP_SEARCH';
// Buildings
export const FETCH_BUILDINGS_STARTED = 'FETCH_BUILDINGS_STARTED';
export const FETCH_BUILDINGS_FAILED = 'FETCH_BUILDINGS_FAILED';
export const FETCH_BUILDINGS = 'FETCH_BUILDINGS';
export const UPDATE_BUILDINGS = 'UPDATE_BUILDINGS';


export function setUser(data) {
    return {type: SET_USER, data};
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
            response = await indicoAxios.get(buildFetchRoomsUrl(), {params});
        } catch (error) {
            handleAxiosError(error);
            dispatch(fetchRoomsFailed(namespace));
            return;
        }
        const {rooms, total} = response.data;
        dispatch(updateRooms(namespace, rooms, total, clear));
    };
}

export function setFilterParameter(namespace, param, data) {
    return {type: SET_FILTER_PARAMETER, namespace, param, data};
}

export function fetchDefaultLocationStarted() {
    return {type: FETCH_DEFAULT_LOCATION_STARTED};
}

export function fetchDefaultLocationFailed() {
    return {type: FETCH_DEFAULT_LOCATION_FAILED};
}

export function updateLocation(location) {
    return {type: UPDATE_LOCATION, location};
}

export function fetchMapDefaultLocation() {
    return async (dispatch) => {
        dispatch(fetchDefaultLocationStarted());

        let response;
        try {
            response = await indicoAxios.get(fetchDefaultLocationUrl());
        } catch (error) {
            handleAxiosError(error);
            dispatch(fetchDefaultLocationFailed());
            return;
        }

        const data = response.data;
        const location = [
            [parseFloat(data.top_left_latitude), parseFloat(data.top_left_longitude)],
            [parseFloat(data.bottom_right_latitude), parseFloat(data.bottom_right_longitude)]
        ];
        dispatch(updateLocation(location));
    };
}

export function toggleMapSearch(search) {
    return {type: TOGGLE_MAP_SEARCH, search};
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
            response = await indicoAxios.get(fetchBuildingsUrl());
        } catch (error) {
            dispatch(fetchBuildingsFailed());
            handleAxiosError(error);
            return;
        }

        dispatch(updateBuildings(response.data));
    };
}
