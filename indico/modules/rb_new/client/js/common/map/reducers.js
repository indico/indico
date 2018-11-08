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
import {getAreaBounds} from './util';


const initialUiState = {
    hoveredRoom: null
};

export default combineReducers({
    request: requestReducer(
        mapActions.FETCH_AREAS_REQUEST,
        mapActions.FETCH_AREAS_SUCCESS,
        mapActions.FETCH_AREAS_ERROR
    ),
    areas: (state = [], action) => {
        switch (action.type) {
            case mapActions.AREAS_RECEIVED:
                return action.data;
            default:
                return state;
        }
    },
    ui: (state = initialUiState, action) => {
        switch (action.type) {
            case mapActions.SET_ROOM_HOVER:
                return {hoveredRoom: action.roomId};
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
        // area updates are global and need to run regardless of the namespace
        if (action.type === mapActions.AREAS_RECEIVED) {
            const defaultArea = action.data.find(area => area.is_default) || action.data[0];
            return {...state, bounds: defaultArea ? getAreaBounds(defaultArea) : null};
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
