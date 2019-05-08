// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

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
