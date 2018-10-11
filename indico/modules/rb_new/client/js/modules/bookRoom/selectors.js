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
import {roomSearchSelectorFactory} from '../../common/roomSearch';
import {selectors as roomsSelectors} from '../../common/rooms';


const {
    getFilters,
    isSearching,
    isSearchFinished,
    getSearchResults,
    getSearchResultIds,
    getTotalResultCount,
    getSearchResultsForMap,
    getAvailabilityDateRange,
    hasUnavailableRooms
} = roomSearchSelectorFactory('bookRoom');

export const isFetchingFormTimeline = ({bookRoom}) => {
    return bookRoom.bookingForm.requests.timeline.state === RequestState.STARTED;
};
export const isFetchingUnavailableRooms = ({bookRoom}) => {
    return bookRoom.unavailableRooms.request.state === RequestState.STARTED;
};
const resolveTimelineRooms = (availability, allRooms) => {
    return availability.map(([roomId, data]) => [roomId, {...data, room: allRooms[data.roomId]}]);
};
export const getUnavailableRoomInfo = createSelector(
    ({bookRoom}) => bookRoom.unavailableRooms.data,
    roomsSelectors.getAllRooms,
    resolveTimelineRooms
);
export const isFetchingTimeline = ({bookRoom}) => bookRoom.timeline.request.state === RequestState.STARTED;
export const isTimelineVisible = ({bookRoom}) => bookRoom.timeline.data.isVisible;
export const getTimelineDateRange = ({bookRoom}) => bookRoom.timeline.data.dateRange;
export const getTimelineAvailability = createSelector(
    ({bookRoom}) => bookRoom.timeline.data.availability,
    roomsSelectors.getAllRooms,
    resolveTimelineRooms,
);
export const hasMoreTimelineData = createSelector(
    getTimelineAvailability,
    ({bookRoom}) => bookRoom.timeline.data.roomIds,
    (availability, roomIds) => roomIds.length > availability.length
);
const getRawSuggestions = ({bookRoom}) => bookRoom.suggestions.data;
export const getSuggestions = createSelector(
    getRawSuggestions,
    roomsSelectors.getAllRooms,
    (suggestions, allRooms) => suggestions.map(suggestion => ({...suggestion, room: allRooms[suggestion.room_id]}))
);
export const getSuggestedRoomIds = createSelector(
    getRawSuggestions,
    suggestions => suggestions.map(x => x.room_id)
);

export {
    getFilters,
    isSearching,
    isSearchFinished,
    getSearchResults,
    getSearchResultIds,
    getTotalResultCount,
    getSearchResultsForMap,
    getAvailabilityDateRange,
    hasUnavailableRooms,
};
