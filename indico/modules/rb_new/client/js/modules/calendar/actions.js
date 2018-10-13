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

import fetchCalendarURL from 'indico-url:rooms_new.calendar';
import searchRoomsURL from 'indico-url:rooms_new.search_rooms';

import _ from 'lodash';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';
import {preProcessParameters} from '../../util';
import {ajaxRules as roomSearchAjaxRules} from '../../common/roomSearch';
import {ajax as ajaxRules} from './serializers';


export const SET_DATE = 'calendar/SET_DATE';
export const SET_MODE = 'calendar/SET_MODE';
export const ROWS_RECEIVED = 'calendar/ROWS_RECEIVED';
export const FETCH_REQUEST = 'calendar/FETCH_REQUEST';
export const FETCH_SUCCESS = 'calendar/FETCH_SUCCESS';
export const FETCH_ERROR = 'calendar/FETCH_ERROR';
export const ROOM_IDS_RECEIVED = 'calendar/ROOM_IDS_RECEIVED';


export function setDate(date) {
    return {type: SET_DATE, date};
}

export function setMode(mode) {
    return {type: SET_MODE, mode};
}

export function fetchCalendar(fetchRooms = true) {
    return async (dispatch, getState) => {
        dispatch({type: FETCH_REQUEST});
        const {calendar: {filters, data: {roomIds}, datePicker}} = getState();
        let newRoomIds = roomIds;

        if (fetchRooms) {
            newRoomIds = null;
            if (!_.isEmpty(filters)) {
                const searchParams = preProcessParameters({...filters}, roomSearchAjaxRules);
                let response;
                try {
                    response = await indicoAxios.get(searchRoomsURL(), {params: searchParams});
                } catch (error) {
                    const message = handleAxiosError(error, true);
                    dispatch({type: FETCH_ERROR, error: message});
                    return;
                }
                newRoomIds = response.data.rooms;
                dispatch({type: ROOM_IDS_RECEIVED, data: newRoomIds});
                if (!newRoomIds.length) {
                    dispatch({type: ROWS_RECEIVED, data: []});
                    dispatch({type: FETCH_SUCCESS});
                    return;
                }
            }
        }

        const params = preProcessParameters(datePicker, ajaxRules);
        return await ajaxAction(
            () => indicoAxios.post(fetchCalendarURL(), {room_ids: newRoomIds}, {params}),
            null,
            [ROWS_RECEIVED, FETCH_SUCCESS],
            [FETCH_ERROR]
        )(dispatch);
    };
}
