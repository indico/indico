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

import fetchConfigURL from 'indico-url:rooms_new.config';
import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';


export const FETCH_REQUEST = 'config/FETCH_REQUEST';
export const FETCH_SUCCESS = 'config/FETCH_SUCCESS';
export const FETCH_ERROR = 'config/FETCH_ERROR';
export const CONFIG_RECEIVED = 'config/CONFIG_RECEIVED';
export const SET_ROOMS_SPRITE_TOKEN = 'config/SET_ROOMS_SPRITE_TOKEN';


export function fetchConfig() {
    return ajaxAction(
        () => indicoAxios.get(fetchConfigURL()),
        FETCH_REQUEST,
        [CONFIG_RECEIVED, FETCH_SUCCESS],
        [FETCH_ERROR]
    );
}

export function setRoomsSpriteToken(token) {
    return {
        type: SET_ROOMS_SPRITE_TOKEN,
        token,
    };
}
