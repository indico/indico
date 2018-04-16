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

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';


export const SET_USER = 'SET_USER';
export const SET_TEXT_FILTER = 'SET_TEXT_FILTER';
export const FETCH_ROOMS_STARTED = 'FETCH_ROOMS_STARTED';
export const FETCH_ROOMS_FAILED = 'FETCH_ROOMS_FAILED';
export const UPDATE_ROOMS = 'UPDATE_ROOMS';
export const SET_FILTER_PARAMETER = 'SET_FILTER_PARAMETER';

export function setUser(data) {
    return {type: SET_USER, data};
}

export function fetchStarted() {
    return {type: FETCH_ROOMS_STARTED};
}

export function fetchFailed() {
    return {type: FETCH_ROOMS_FAILED};
}

export function updateRooms(rooms) {
    return {type: UPDATE_ROOMS, rooms};
}

export function fetchRooms(reducerName) {
    return async (dispatch, getStore) => {
        dispatch(fetchStarted());

        const {staticData: {fetchRoomsUrl}} = getStore();
        const {filters: {text}} = getStore()[reducerName];
        let response;
        const params = {};
        if (text) {
            params.room_name = text;
        }

        try {
            response = await indicoAxios.get(fetchRoomsUrl, {params});
        } catch (error) {
            handleAxiosError(error);
            dispatch(fetchFailed());
            return;
        }

        dispatch(updateRooms(response.data));
    };
}

export function setFilterParameter(namespace, param, data) {
    return {type: SET_FILTER_PARAMETER, namespace, param, data};
}
