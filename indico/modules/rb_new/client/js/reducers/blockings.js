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

import {combineReducers} from 'redux';

import filterReducerFactory from './roomBooking/filters';
import * as actions from '../actions';


const initialState = {
    list: [],
    isFetching: false
};

function blockingsReducer(state = initialState, action) {
    switch (action.type) {
        case actions.UPDATE_BLOCKINGS:
            return {...state, isFetching: false, list: action.blockings};
        case actions.FETCH_BLOCKINGS_STARTED:
            return {...state, isFetching: true};
        case actions.FETCH_BLOCKINGS_FAILED:
            return {...state, isFetching: false};
        default:
            return state;
    }
}

export default combineReducers({
    blockings: blockingsReducer,
    filters: filterReducerFactory('blockingList')
});
