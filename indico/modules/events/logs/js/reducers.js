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

import * as actions from './actions';


const initialState = {
    entries: [],
    keyword: null,
    page: 1,
    isFetching: false,
    filters: {
        event: true,
        management: true,
        email: true,
        participants: true
    }
};

export default function globalEventLogReducer(state, action) {
    if (typeof state === 'undefined') {
        return initialState;
    }

    switch (action.type) {
        case actions.SET_KEYWORD:
            return { ...state, keyword: action.keyword };
        case actions.SET_FILTER:
            return { ...state, filter: action.filter };
        case actions.SET_PAGE:
            return { ...state, page: action.page };
        case actions.UPDATE_ENTRIES:
            return { ...state, entries: action.entries };
        default:
            return state;
    }
}
