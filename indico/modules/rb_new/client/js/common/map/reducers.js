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
import {requestReducer} from 'indico/utils/redux';
import * as mapActions from './actions';
import * as globalActions from '../../actions';
import {getAspectBounds} from './util';


export default combineReducers({
    request: requestReducer(
        mapActions.FETCH_ASPECTS_REQUEST,
        mapActions.FETCH_ASPECTS_SUCCESS,
        mapActions.FETCH_ASPECTS_ERROR
    ),
    aspects: (state = [], action) => {
        switch (action.type) {
            case mapActions.ASPECTS_RECEIVED:
                return action.data;
            default:
                return state;
        }
    }
});

export function mapSearchReducerFactory(namespace) {
    const initialState = {
        bounds: null,
        search: false,
    };

    return (state = initialState, action) => {
        // aspect updates are global and need to run regardless of the namespace
        if (action.type === mapActions.ASPECTS_RECEIVED) {
            const defaultAspect = action.data.find(aspect => aspect.default_on_startup) || action.data[0];
            return {...state, bounds: defaultAspect ? getAspectBounds(defaultAspect) : null};
        }

        if (action.namespace !== namespace) {
            return state;
        }

        switch (action.type) {
            case mapActions.UPDATE_LOCATION:
                return {...state, bounds: action.location};
            case mapActions.TOGGLE_MAP_SEARCH:
                return {...state, search: action.search};
            case globalActions.RESET_PAGE_STATE:
                return {...state, search: false};
            default:
                return state;
        }
    };
}
