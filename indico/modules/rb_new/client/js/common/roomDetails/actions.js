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

import fetchRoomDetailsURL from 'indico-url:rooms_new.room_details';
import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';


export const DETAILS_RECEIVED = 'roomDetails/DETAILS_RECEIVED';
export const FETCH_REQUEST = 'roomDetails/FETCH_REQUEST';
export const FETCH_SUCCESS = 'roomDetails/FETCH_SUCCESS';
export const FETCH_ERROR = 'roomDetails/FETCH_ERROR';


export function fetchDetails(id) {
    return async (dispatch, getStore) => {
        const {roomDetails: {rooms}} = getStore();
        if (id in rooms) {
            return;
        }
        return await ajaxAction(
            () => indicoAxios.get(fetchRoomDetailsURL({room_id: id})),
            FETCH_REQUEST,
            [DETAILS_RECEIVED, FETCH_SUCCESS],
            FETCH_ERROR
        )(dispatch);
    };
}
