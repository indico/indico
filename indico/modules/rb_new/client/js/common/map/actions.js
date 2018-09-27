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

import fetchMapAspectsURL from 'indico-url:rooms_new.default_aspects';

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';
import * as mapSelectors from './selectors';


export const UPDATE_LOCATION = 'map/UPDATE_LOCATION';
export const TOGGLE_MAP_SEARCH = 'map/TOGGLE_SEARCH';

export const FETCH_ASPECTS_REQUEST = 'map/FETCH_ASPECTS_REQUEST';
export const FETCH_ASPECTS_SUCCESS = 'map/FETCH_ASPECTS_SUCCESS';
export const FETCH_ASPECTS_ERROR = 'map/FETCH_ASPECTS_ERROR';
export const ASPECTS_RECEIVED = 'map/ASPECTS_RECEIVED';


export function updateLocation(namespace, location) {
    return {type: UPDATE_LOCATION, location, namespace};
}

export function toggleMapSearch(namespace, search) {
    return {type: TOGGLE_MAP_SEARCH, search, namespace};
}

export function fetchAspects() {
    return async (dispatch, getStore) => {
        if (!mapSelectors.isMapEnabled(getStore())) {
            return;
        }

        return await ajaxAction(
            () => indicoAxios.get(fetchMapAspectsURL()),
            FETCH_ASPECTS_REQUEST,
            [ASPECTS_RECEIVED, FETCH_ASPECTS_SUCCESS],
            FETCH_ASPECTS_ERROR
        )(dispatch);
    };
}
