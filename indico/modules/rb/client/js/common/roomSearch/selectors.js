// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSelector} from 'reselect';

import {RequestState} from 'indico/utils/redux';

import {selectors as roomsSelectors} from '../rooms';

export function roomSearchSelectorFactory(namespace) {
  const getFilters = ({[namespace]: stateSlice}) => stateSlice.filters;
  const getSearchResultIds = ({[namespace]: stateSlice}) => stateSlice.search.results.rooms;
  const getSearchResultIdsWithoutAvailabilityFilter = ({[namespace]: stateSlice}) =>
    stateSlice.search.results.roomsWithoutAvailabilityFilter;
  const getTotalResultCount = ({[namespace]: stateSlice}) => stateSlice.search.results.total;
  const getAvailabilityDateRange = ({[namespace]: stateSlice}) =>
    stateSlice.search.results.availabilityDays;
  const isSearching = ({[namespace]: stateSlice}) =>
    stateSlice.search.request.state === RequestState.STARTED;
  const isSearchFinished = ({[namespace]: stateSlice}) =>
    stateSlice.search.request.state === RequestState.SUCCESS;

  const getSearchResults = createSelector(
    getSearchResultIds,
    roomsSelectors.getAllRooms,
    (roomIds, allRooms) => roomIds.map(id => allRooms[id])
  );

  const getSearchResultsForMap = createSelector(
    getSearchResults,
    rooms =>
      rooms
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
