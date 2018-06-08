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


import * as actions from '../actions';


const initialState = {
    filters: {}
};

export default function reducer(state = initialState, action) {
    // reset open dropdowns on page reload
    if (action.type === '@@router/LOCATION_CHANGE') {
        return {...state, filters: {}};
    }

    switch (action.type) {
        case actions.OPEN_FILTER_DROPDOWN:
            return {...state, filters: {[action.name]: true}};
        case actions.CLOSE_FILTER_DROPDOWN:
            return {...state, filters: {}};
        default:
            return state;
    }
}
