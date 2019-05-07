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

import getMapAreasURL from 'indico-url:rb.map_areas';

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';
import * as mapSelectors from './selectors';


export const UPDATE_LOCATION = 'map/UPDATE_LOCATION';
export const TOGGLE_MAP_SEARCH = 'map/TOGGLE_SEARCH';

export const FETCH_AREAS_REQUEST = 'map/FETCH_AREAS_REQUEST';
export const FETCH_AREAS_SUCCESS = 'map/FETCH_AREAS_SUCCESS';
export const FETCH_AREAS_ERROR = 'map/FETCH_AREAS_ERROR';
export const AREAS_RECEIVED = 'map/AREAS_RECEIVED';
export const SET_ROOM_HOVER = `map/SET_ROOM_HOVER`;


export function updateLocation(namespace, location) {
    return {type: UPDATE_LOCATION, location, namespace};
}

export function toggleMapSearch(namespace, search) {
    return {type: TOGGLE_MAP_SEARCH, search, namespace};
}

export function setRoomHover(roomId) {
    return {type: SET_ROOM_HOVER, roomId};
}

export function fetchAreas() {
    return async (dispatch, getStore) => {
        if (!mapSelectors.isMapEnabled(getStore())) {
            return;
        }

        return await ajaxAction(
            () => indicoAxios.get(getMapAreasURL()),
            FETCH_AREAS_REQUEST,
            [AREAS_RECEIVED, FETCH_AREAS_SUCCESS],
            FETCH_AREAS_ERROR
        )(dispatch);
    };
}
