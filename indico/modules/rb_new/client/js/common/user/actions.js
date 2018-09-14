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

import fetchUserInfoURL from 'indico-url:rooms_new.user_info';
import favoriteRoomsURL from 'indico-url:rooms_new.favorite_rooms';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {setMomentLocale} from 'indico/utils/date';
import {ajaxAction} from 'indico/utils/redux';


export const FETCH_USER_INFO_REQUEST = 'user/FETCH_USER_INFO_REQUEST';
export const FETCH_USER_INFO_SUCCESS = 'user/FETCH_USER_INFO_SUCCESS';
export const FETCH_USER_INFO_ERROR = 'user/FETCH_USER_INFO_ERROR';
export const USER_INFO_RECEIVED = 'user/USER_INFO_RECEIVED';

export const FETCH_FAVORITES_REQUEST = 'user/FETCH_FAVORITES_REQUEST';
export const FETCH_FAVORITES_SUCCESS = 'user/FETCH_FAVORITES_SUCCESS';
export const FETCH_FAVORITES_ERROR = 'user/FETCH_FAVORITES_ERROR';
export const FAVORITES_RECEIVED = 'user/FAVORITES_RECEIVED';

export const ADD_FAVORITE_ROOM = 'user/ADD_FAVORITE_ROOM';
export const DEL_FAVORITE_ROOM = 'user/DEL_FAVORITE_ROOM';


export function fetchUserInfo() {
    return async (dispatch) => {
        const result = await ajaxAction(
            () => indicoAxios.get(fetchUserInfoURL()),
            FETCH_USER_INFO_REQUEST,
            [USER_INFO_RECEIVED, FETCH_USER_INFO_SUCCESS],
            FETCH_USER_INFO_ERROR
        )(dispatch);

        await setMomentLocale(result.data.language);
        return result;
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
    return ajaxAction(
        () => indicoAxios.get(favoriteRoomsURL()),
        FETCH_FAVORITES_REQUEST,
        [FAVORITES_RECEIVED, FETCH_FAVORITES_SUCCESS],
        FETCH_FAVORITES_ERROR
    );
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
