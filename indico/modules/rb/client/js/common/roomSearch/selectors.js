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
import {RequestState} from 'indico/utils/redux';
import {selectors as roomsSelectors} from '../rooms';


export function roomSearchSelectorFactory(namespace) {
    const getFilters = ({[namespace]: stateSlice}) => stateSlice.filters;
    const getSearchResultIds = ({[namespace]: stateSlice}) => stateSlice.search.results.rooms;
    const getSearchResultIdsWithoutAvailabilityFilter =
        ({[namespace]: stateSlice}) => stateSlice.search.results.roomsWithoutAvailabilityFilter;
    const getTotalResultCount = ({[namespace]: stateSlice}) => stateSlice.search.results.total;
    const getAvailabilityDateRange = ({[namespace]: stateSlice}) => stateSlice.search.results.availabilityDays;
    const isSearching = ({[namespace]: stateSlice}) => stateSlice.search.request.state === RequestState.STARTED;
    const isSearchFinished = ({[namespace]: stateSlice}) => stateSlice.search.request.state === RequestState.SUCCESS;

    const getSearchResults = createSelector(
        getSearchResultIds,
        roomsSelectors.getAllRooms,
        (roomIds, allRooms) => roomIds.map(id => allRooms[id])
    );

    const getSearchResultsForMap = createSelector(
        getSearchResults,
        rooms => rooms
            .filter(room => room.latitude !== null && room.longitude !== null)
            .map(room => ({
                id: room.id,
                name: room.name,
                building: room.building,
                floor: room.floor,
                number: room.number,
                fullName: room.fullName,
                lat: room.latitude,
                lng: room.longitude,
                canUserBook: room.canUserBook,
            }))
    );

    return {
        getFilters,
        isSearching,
        isSearchFinished,
        getSearchResults,
        getSearchResultIds,
        getSearchResultIdsWithoutAvailabilityFilter,
        getTotalResultCount,
        getSearchResultsForMap,
        getAvailabilityDateRange,
    };
}
