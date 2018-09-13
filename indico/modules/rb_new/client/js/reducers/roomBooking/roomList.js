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
    matching: 0,
    isFetching: false,
    isLoadingMore: null,
    total: 0
};


function mergeRooms(state, action) {
    const {list: oldList} = state;
    const {loadMore, matching, total, rooms: newList} = action;
    return {
        matching,
        total,
        list: loadMore ? oldList.concat(newList) : newList
    };
}


export function roomsReducerFactory(namespace) {
    return (state = initialRoomsState, action) => {
        if (action.namespace !== namespace) {
            return state;
        }

        switch (action.type) {
            case actions.SEARCH_ROOMS_STARTED:
                return {...state, isFetching: true, isLoadingMore: action.loadMore};
            case actions.SEARCH_ROOMS_FAILED:
                return {...state, isFetching: false, isLoadingMore: null};
            case actions.UPDATE_ROOMS:
                return {...state, isFetching: false, isLoadingMore: null, ...mergeRooms(state, action)};
            default:
                return state;
        }
    };
}
