// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSelector} from 'reselect';

import {getNumDays} from './util';

export const getStaticData = state => state.staticData;
export const getEntries = state => state.entries;
export const getNavigation = state => state.navigation;
export const getDisplayMode = state => state.displayMode;

export const getEventStartDt = createSelector(
  getStaticData,
  staticData => staticData.startDt
);
export const getEventEndDt = createSelector(
  getStaticData,
  staticData => staticData.endDt
);
export const getEventNumDays = createSelector(
  getEventStartDt,
  getEventEndDt,
  (startDt, endDt) => getNumDays(startDt, endDt) + 1
);

export const getSessionBlocks = createSelector(
  getEntries,
  entries => entries.sessionBlocks
);
export const getContributions = createSelector(
  getEntries,
  entries => entries.contributions
);
export const getAllEntries = createSelector(
  getSessionBlocks,
  getContributions,
  (sessionBlocks, contributions) => [...sessionBlocks, ...contributions]
);

export const getNavbarMaxDays = createSelector(
  getNavigation,
  navigation => navigation.numDays
);
export const getNavbarOffset = createSelector(
  getNavigation,
  navigation => navigation.offset
);
