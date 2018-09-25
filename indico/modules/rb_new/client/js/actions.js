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

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import * as selectors from './selectors';


// Page state
export const INIT = 'INIT';
export const RESET_PAGE_STATE = 'RESET_PAGE_STATE';
// Filter
export const SET_FILTER_PARAMETER = 'SET_FILTER_PARAMETER';
export const SET_FILTERS = 'SET_FILTERS';
// Map
export const FETCH_MAP_ASPECTS_STARTED = 'FETCH_MAP_ASPECTS_STARTED';
export const FETCH_MAP_ASPECTS_FAILED = 'FETCH_MAP_ASPECTS_FAILED';
export const UPDATE_ASPECTS = 'UPDATE_ASPECTS';
export const UPDATE_LOCATION = 'UPDATE_LOCATION';
export const TOGGLE_MAP_SEARCH = 'TOGGLE_MAP_SEARCH';


export function init() {
    return {type: INIT};
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
    return async (dispatch, getStore) => {
        if (!selectors.isMapEnabled(getStore())) {
            return;
        }

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
