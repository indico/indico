// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

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
