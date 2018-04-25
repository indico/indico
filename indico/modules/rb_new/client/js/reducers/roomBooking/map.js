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

import * as actions from '../../actions';


const initialState = {
    bounds: null,
    aspects: [],
    search: true,
    isFetching: false,
};


export default function mapReducer(state = initialState, action) {
    switch (action.type) {
        case actions.FETCH_DEFAULT_ASPECTS_STARTED:
            return {...state, isFetching: true};
        case actions.FETCH_DEFAULT_ASPECTS_FAILED:
            return {...state, isFetching: false};
        case actions.UPDATE_ASPECTS:
            return {...state, aspects: action.aspects, isFetching: false};
        case actions.UPDATE_LOCATION:
            return {...state, bounds: action.location, isFetching: false};
        case actions.TOGGLE_MAP_SEARCH:
            return {...state, search: action.search};
        default:
            return state;
    }
}
