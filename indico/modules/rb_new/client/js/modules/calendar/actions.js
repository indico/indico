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
import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';
import {preProcessParameters} from '../../util';
import {ajax as ajaxRules} from './serializers';


export const SET_DATE = 'calendar/SET_DATE';
export const ROWS_RECEIVED = 'calendar/ROWS_RECEIVED';
export const FETCH_REQUEST = 'calendar/FETCH_REQUEST';
export const FETCH_SUCCESS = 'calendar/FETCH_SUCCESS';
export const FETCH_ERROR = 'calendar/FETCH_ERROR';


export function setDate(date) {
    return {type: SET_DATE, date};
}

export function fetchCalendar() {
    return async (dispatch, getState) => {
        const {calendar: {data}} = getState();
        const params = preProcessParameters(data, ajaxRules);
        return await ajaxAction(
            () => indicoAxios.get(fetchCalendarURL(params)),
            FETCH_REQUEST,
            [ROWS_RECEIVED, FETCH_SUCCESS],
            [FETCH_ERROR]
        )(dispatch);
    };
}
