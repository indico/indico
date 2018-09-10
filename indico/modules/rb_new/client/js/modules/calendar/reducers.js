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

import moment from 'moment';
import {combineReducers} from 'redux';

import {requestReducer} from 'indico/utils/redux';
import * as actions from '../../actions';
import * as calendarActions from './actions';


export const initialState = {
    date: moment().format('YYYY-MM-DD'),
    rows: [],
};

export default combineReducers({
    request: requestReducer(calendarActions.FETCH_REQUEST, calendarActions.FETCH_SUCCESS, calendarActions.FETCH_ERROR),
    data: (state = initialState, action) => {
        switch (action.type) {
            case actions.RESET_PAGE_STATE:
                return action.namespace === 'calendar' ? initialState : state;
            case calendarActions.SET_DATE:
                return {...state, rows: [], date: action.date};
            case calendarActions.ROWS_RECEIVED:
                return {...state, rows: action.data};
            default:
                return state;
        }
    }
});
