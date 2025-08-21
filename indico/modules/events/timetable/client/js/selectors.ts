// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSelector} from 'reselect';

import {ReduxState} from './reducers';
import {appendSessionAttributes, mergeChanges} from './util';
import {getDateKey} from './utils';

export const getStaticData = state => state.staticData;
export const getEntries = (state: ReduxState) => state.entries;
export const getDayEntries = (state: ReduxState) =>
  state.entries.changes[state.entries.currentChangeIdx].entries;
export const getSessions = state => state.sessions;
export const getNavigation = state => state.navigation;
export const getDisplay = state => state.display;
export const getLatestChange = (state: ReduxState) =>
  state.entries.changes[state.entries.currentChangeIdx];

export const getNumUnscheduled = (state: ReduxState) =>
  state.entries.changes[state.entries.currentChangeIdx].unscheduled.length;

// Get the selected entry ID
// You should not use this selector directly, use makeIsSelectedSelector instead
// to check if an entry is selected
export const getSelectedId = (state: ReduxState) => state.entries.selectedId;
export const getCurrentDate = (state: ReduxState) => state.navigation.currentDate;

export const makeIsSelectedSelector = () =>
  createSelector(
    [getSelectedId, (_state: ReduxState, id: number) => id],
    (selectedId, id) => selectedId === id
  );

export const getEventId = createSelector(
  getStaticData,
  staticData => {
    return staticData.eventId;
  }
);
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
  (startDt, endDt) => endDt.diff(startDt, 'days') + 1
);

export const getCurrentDayEntries = createSelector(
  getDayEntries,
  getCurrentDate,
  (entries, currentDate) => entries[getDateKey(currentDate)]
);
export const getBlocks = createSelector(
  getEntries,
  getSessions,
  (entries, sessions) => appendSessionAttributes(entries.blocks, sessions)
);
export const getChildren = createSelector(
  getEntries,
  getSessions,
  (entries, sessions) => appendSessionAttributes(entries.children, sessions)
);

export const getVisibleChildren = createSelector(
  getChildren,
  children => children.filter(c => !c.isPoster)
);
export const getUnscheduled = createSelector(
  getLatestChange,
  getSessions,
  (entries, sessions) => appendSessionAttributes(entries.unscheduled, sessions)
);
// export const getNumUnscheduled = createSelector(
//   getUnscheduled,
//   unscheduled => unscheduled.length
// );
export const getVisibleEntries = createSelector(
  getBlocks,
  getVisibleChildren,
  (blocks, children) => [...blocks, ...children]
);
export const getSelectedEntry = createSelector(
  getDayEntries,
  getSelectedId,
  (entries, id) => {
    entries = Object.values(entries).flatMap(x => x);
    entries = entries.flatMap(e => (e.type === 'block' ? [e, ...e.children] : [e]));
    return entries.find(e => e.id === id);
  }
);
export const getDraftEntry = createSelector(
  getEntries,
  entries => entries.draftEntry
);
export const canUndo = createSelector(
  getEntries,
  entries => entries.currentChangeIdx > 0
);
export const canRedo = createSelector(
  getEntries,
  entries => entries.currentChangeIdx < entries.changes.length - 1
);
export const getMergedChanges = createSelector(
  getEntries,
  getSessions,
  (entries, sessions) => mergeChanges(entries, sessions)
);
export const getError = createSelector(
  getEntries,
  entries => entries.error
);

export const showUnscheduled = createSelector(
  getDisplay,
  display => display.showUnscheduled
);

export const getDefaultContribDurationMinutes = createSelector(
  getStaticData,
  staticData => staticData.defaultContribDurationMinutes
);

// Navigation state
export const getIsExpanded = createSelector(
  getNavigation,
  navigation => navigation.isExpanded
);
export const getIsDraft = createSelector(
  getNavigation,
  navigation => navigation.isDraft
);
