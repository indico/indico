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
import fetchMapRoomsUrl from 'indico-url:rooms_new.map_rooms';
import fetchDefaultAspectsUrl from 'indico-url:rooms_new.default_aspects';
import fetchBuildingsUrl from 'indico-url:rooms_new.buildings';
import favoriteRoomsUrl from 'indico-url:rooms_new.favorite_rooms';
import equipmentTypesUrl from 'indico-url:rooms_new.equipment_types';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {getAspectBounds, preProcessParameters} from './util';
import {ajax as ajaxFilterRules} from './serializers/filters';


// User
export const SET_FAVORITE_ROOMS = 'SET_FAVORITE_ROOMS';
export const ADD_FAVORITE_ROOM = 'ADD_FAVORITE_ROOM';
export const DEL_FAVORITE_ROOM = 'DEL_FAVORITE_ROOM';
// Filter
export const SET_FILTER_PARAMETER = 'SET_FILTER_PARAMETER';
// Rooms
export const FETCH_ROOMS_STARTED = 'FETCH_ROOMS_STARTED';
export const FETCH_ROOMS_FAILED = 'FETCH_ROOMS_FAILED';
export const UPDATE_ROOMS = 'UPDATE_ROOMS';
export const FETCH_MAP_ROOMS_STARTED = 'FETCH_MAP_ROOMS_STARTED';
export const FETCH_MAP_ROOMS_FAILED = 'FETCH_MAP_ROOMS_FAILED';
export const UPDATE_MAP_ROOMS = 'UPDATE_MAP_ROOMS';
// Equipment types
export const SET_EQUIPMENT_TYPES = 'SET_EQUIPMENT_TYPES';
// Map
export const FETCH_DEFAULT_ASPECTS_STARTED = 'FETCH_DEFAULT_ASPECTS_STARTED';
export const FETCH_DEFAULT_ASPECTS_FAILED = 'FETCH_DEFAULT_ASPECTS_FAILED';
export const UPDATE_ASPECTS = 'UPDATE_ASPECTS';
export const UPDATE_LOCATION = 'UPDATE_LOCATION';
export const TOGGLE_MAP_SEARCH = 'TOGGLE_MAP_SEARCH';
// Buildings
export const FETCH_BUILDINGS_STARTED = 'FETCH_BUILDINGS_STARTED';
export const FETCH_BUILDINGS_FAILED = 'FETCH_BUILDINGS_FAILED';
export const FETCH_BUILDINGS = 'FETCH_BUILDINGS';
export const UPDATE_BUILDINGS = 'UPDATE_BUILDINGS';


export function fetchEquipmentTypes() {
    return async (dispatch) => {
        let response;
        try {
            response = await indicoAxios.get(equipmentTypesUrl());
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
            url: favoriteRoomsUrl(id !== null ? {room_id: id} : {})
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
            response = await indicoAxios.get(fetchMapRoomsUrl(), {params});
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

export function setFilterParameter(namespace, param, data) {
    return {type: SET_FILTER_PARAMETER, namespace, param, data};
}

export function fetchDefaultAspectsStarted(namespace) {
    return {type: FETCH_DEFAULT_ASPECTS_STARTED, namespace};
}

export function fetchDefaultAspectsFailed(namespace) {
    return {type: FETCH_DEFAULT_ASPECTS_FAILED, namespace};
}

export function updateAspects(namespace, aspects) {
    return {type: UPDATE_ASPECTS, aspects, namespace};
}

export function updateLocation(namespace, location) {
    return {type: UPDATE_LOCATION, location, namespace};
}

export function fetchMapDefaultAspects(namespace) {
    return async (dispatch) => {
        dispatch(fetchDefaultAspectsStarted(namespace));

        let response;
        try {
            response = await indicoAxios.get(fetchDefaultAspectsUrl());
        } catch (error) {
            handleAxiosError(error);
            dispatch(fetchDefaultAspectsFailed(namespace));
            return;
        }

        dispatch(updateAspects(namespace, response.data));
        const defaultAspect = response.data.find(aspect => aspect.default_on_startup);
        dispatch(updateLocation(namespace, getAspectBounds(defaultAspect)));
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
            response = await indicoAxios.get(fetchBuildingsUrl());
        } catch (error) {
            dispatch(fetchBuildingsFailed());
            handleAxiosError(error);
            return;
        }

        dispatch(updateBuildings(response.data));
    };
}
