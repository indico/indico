// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import {createSelector} from 'reselect';
import {RequestState} from 'indico/utils/redux';
import {roomSearchSelectorFactory} from '../../common/roomSearch';
import {selectors as roomsSelectors} from '../../common/rooms';
import {selectors as userSelectors} from '../../common/user';

const {
  getFilters,
  isSearching,
  isSearchFinished,
  getSearchResults,
  getSearchResultIds,
  getSearchResultIdsWithoutAvailabilityFilter,
  getTotalResultCount,
  getSearchResultsForMap: getAllSearchResultsForMap,
  getAvailabilityDateRange,
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
export const isFetchingTimeline = ({bookRoom}) =>
  bookRoom.timeline.request.state === RequestState.STARTED;
export const isTimelineVisible = ({bookRoom}) => bookRoom.timeline.data.isVisible;
export const getTimelineDateRange = ({bookRoom}) => bookRoom.timeline.datePicker.dateRange;
export const getTimelineDatePicker = ({bookRoom}) => bookRoom.timeline.datePicker;
export const getUnavailableDatePicker = ({bookRoom}) => bookRoom.unavailableRooms.datePicker;
export const getTimelineAvailability = createSelector(
  ({bookRoom}) => bookRoom.timeline.data.availability,
  roomsSelectors.getAllRooms,
  resolveTimelineRooms
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
  userSelectors.getUnbookableRoomIds,
  (suggestions, allRooms, unbookableRoomIds) => {
    const unbookable = new Set(unbookableRoomIds);
    return suggestions
      .filter(suggestion => !unbookable.has(suggestion.room_id))
      .map(suggestion => ({...suggestion, room: allRooms[suggestion.room_id]}));
  }
);
export const getSuggestedRoomIds = createSelector(
  getRawSuggestions,
  userSelectors.getUnbookableRoomIds,
  (suggestions, unbookableRoomIds) => {
    const unbookable = new Set(unbookableRoomIds);
    return suggestions.filter(x => !unbookable.has(x.room_id)).map(x => x.room_id);
  }
);

export const getBookingFormAvailability = ({bookRoom}) => bookRoom.bookingForm.availability;
export const getBookingFormRelatedEvents = ({bookRoom}) => bookRoom.bookingForm.relatedEvents;

export const isSearchingOrCheckingPermissions = createSelector(
  isSearching,
  userSelectors.isCheckingUserRoomPermissions,
  (searching, checkingPermissions) => searching || checkingPermissions
);
export const isSearchAndPermissionCheckFinished = createSelector(
  isSearchFinished,
  userSelectors.isCheckingUserRoomPermissions,
  (searchFinished, checkingPermissions) => searchFinished && !checkingPermissions
);

/** Get rooms ids that are unbookable by the user and also take into
 *  account the maximum advance days property of the room
 */
export const getUnbookableRoomIdsWithMaxAdvanceDays = createSelector(
  userSelectors.getUnbookableRoomIds,
  roomsSelectors.getAllRooms,
  getFilters,
  (unbookableRoomIds, rooms, {dates: {startDate}}) => {
    const roomIds = Object.entries(rooms)
      .filter(([, room]) => !room.canUserOverride && room.maxAdvanceDays)
      .filter(([, room]) => moment(startDate) > moment().add(room.maxAdvanceDays, 'days'))
      .map(([id]) => +id);
    return [...new Set([...roomIds, ...unbookableRoomIds])];
  }
);

/**
 * Get the room ids which are matching the filter criteria and bookable
 * by the user during the selected time slot.
 */
export const getSearchResultIdsWithoutUnbookable = createSelector(
  getSearchResultIds,
  getUnbookableRoomIdsWithMaxAdvanceDays,
  (roomIds, unbookableRoomIds) => {
    const unbookable = new Set(unbookableRoomIds);
    return roomIds.filter(id => !unbookable.has(id));
  }
);

/**
 * Get the rooms which are matching the filter criteria and bookable by
 * the user during the selected time slot.
 */
export const getSearchResultsWithoutUnbookable = createSelector(
  getSearchResultIdsWithoutUnbookable,
  roomsSelectors.getAllRooms,
  (roomIds, allRooms) => roomIds.map(id => allRooms[id])
);

/**
 * Get the total number of rooms matching the filter criteria except
 * those the user is unauthorized to book.
 */
const getTotalResultCountWithoutUnbookable = createSelector(
  getSearchResultIdsWithoutAvailabilityFilter,
  getUnbookableRoomIdsWithMaxAdvanceDays,
  (roomIds, unbookableRoomIds) => {
    const unbookable = new Set(unbookableRoomIds);
    return roomIds.filter(id => !unbookable.has(id)).length;
  }
);

/** Get the number of rooms the user is not authorized to book */
export const getUnbookableResultCount = createSelector(
  getSearchResultIdsWithoutAvailabilityFilter,
  getTotalResultCountWithoutUnbookable,
  (roomIds, bookableCount) => roomIds.length - bookableCount
);

/**
 * Get the map data for the current result list without unbookable ones.
 */
export const getSearchResultsForMap = createSelector(
  getAllSearchResultsForMap,
  getUnbookableRoomIdsWithMaxAdvanceDays,
  (mapResults, unbookableRoomIds) => {
    const unbookable = new Set(unbookableRoomIds);
    return mapResults.filter(x => !unbookable.has(x.id));
  }
);

export {
  getFilters,
  isSearching,
  isSearchFinished,
  getSearchResults,
  getSearchResultIds,
  getTotalResultCount,
  getAvailabilityDateRange,
};
