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
import * as actions from './actions';


const initialState = {
    entries: [],
    entryIndex: new Map(),
    keyword: null,
    currentPage: 1,
    isFetching: false,
    filters: {
        event: true,
        management: true,
        emails: true,
        participants: true,
        reviewing: true
    },
    pages: [],
    currentViewIndex: null
};

function _buildDateIndex(entries) {
    return entries.reduce((accum, entry, index) => {
        const date = moment(entry.time).format('YYYYMMDD');
        if (accum.has(date)) {
            accum.get(date).push(entry);
        } else {
            accum.set(date, [entry]);
        }
        entry.index = index;
        return accum;
    }, new Map());
}

function logReducer(state = initialState, action) {
    switch (action.type) {
        case actions.SET_KEYWORD:
            return {...state, keyword: action.keyword};
        case actions.SET_FILTER:
            return {...state, filters: {...state.filters, ...action.filter}};
        case actions.SET_PAGE:
            return {...state, currentPage: action.currentPage};
        case actions.UPDATE_ENTRIES:
            return {
                ...state,
                entries: action.entries,
                entryIndex: _buildDateIndex(action.entries),
                pages: action.pages,
                isFetching: false,
            };
        case actions.FETCH_STARTED:
            return {...state, isFetching: true};
        case actions.FETCH_FAILED:
            return {...state, isFetching: false};
        case actions.SET_DETAILED_VIEW:
            return {...state, currentViewIndex: action.currentViewIndex};
        default:
            return state;
    }
}


export default combineReducers({
    logs: logReducer,
    staticData: (state = {}) => state,
});
