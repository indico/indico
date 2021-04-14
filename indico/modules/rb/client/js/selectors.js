// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSelector} from 'reselect';

import {selectors as configSelectors} from './common/config';
import {selectors as roomsSelectors} from './common/rooms';
import {selectors as userSelectors} from './common/user';

export const isInitializing = createSelector(
  configSelectors.hasLoadedConfig,
  userSelectors.hasLoadedUserInfo,
  roomsSelectors.hasLoadedRooms,
  roomsSelectors.hasLoadedEquipmentTypes,
  (...ready) => ready.some(x => !x)
);

export function filtersAreSet(state) {
  // check that recurrence + start date + start/end time are set
  const {
    filters: {
      recurrence,
      dates: {startDate},
    },
  } = state.bookRoom;
  return !!(recurrence.type && startDate);
}
