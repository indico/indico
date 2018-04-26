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


const initialRoomsState = {
    list: [],
    total: 0,
    isFetching: false
};


function mergeRooms(state, action) {
    const {list: oldRooms} = state;
    const {clear, total, rooms: newRooms} = action;
    return {
        total,
        list: clear ? newRooms : oldRooms.concat(newRooms)
    };
}


export function roomsReducerFactory(namespace) {
    return (state = initialRoomsState, action) => {
        if (action.namespace !== namespace) {
            return state;
        }

        switch (action.type) {
            case actions.FETCH_ROOMS_STARTED:
                return {...state, isFetching: true};
            case actions.FETCH_ROOMS_FAILED:
                return {...state, isFetching: false};
            case actions.UPDATE_ROOMS:
                return {...state, isFetching: false, ...mergeRooms(state, action)};
            default:
                return state;
        }
    };
}


const initialBuildingsState = {
    list: [],
    isFetching: false
};

export function buildingsReducer(state = initialBuildingsState, action) {
    switch (action.type) {
        case actions.UPDATE_BUILDINGS:
            return {...state, isFetching: false, list: action.buildings};
        case actions.FETCH_BUILDINGS_STARTED:
            return {...state, isFetching: true};
        case actions.FETCH_BUILDINGS_FAILED:
            return {...state, isFetching: false};
        default:
            return state;
    }
}
