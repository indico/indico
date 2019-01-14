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

import {createSelector} from 'reselect';

import {roomSearchSelectorFactory} from '../../common/roomSearch';
import {selectors as userSelectors} from '../../common/user';


const {
    getFilters,
    isSearching,
    getSearchResults: getAllSearchResults,
    getSearchResultsForMap: getAllSearchResultsForMap,
} = roomSearchSelectorFactory('roomList');

export const getSearchResults = createSelector(
    getAllSearchResults,
    getFilters,
    userSelectors.getUnbookableRoomIds,
    (results, {onlyAuthorized}, unbookableRoomIds) => {
        if (!onlyAuthorized) {
            return results;
        }
        const unbookable = new Set(unbookableRoomIds);
        return results.filter(room => !unbookable.has(room.id));
    }
);

export const getSearchResultsForMap = createSelector(
    getAllSearchResultsForMap,
    getFilters,
    userSelectors.getUnbookableRoomIds,
    (results, {onlyAuthorized}, unbookableRoomIds) => {
        if (!onlyAuthorized) {
            return results;
        }
        const unbookable = new Set(unbookableRoomIds);
        return results.filter(room => !unbookable.has(room.id));
    }
);

export {getFilters, isSearching};
