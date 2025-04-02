// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSelector} from 'reselect';

import {ReduxState} from './reducers';
import {appendSessionAttributes, mergeChanges} from './util';

export const getStaticData = state => state.staticData;
export const getEntries = (state: ReduxState) => state.entries;
export const getDayEntries = (state: ReduxState) =>
  state.entries.changes[state.entries.currentChangeIdx].entries;
export const getSessions = state => state.sessions;
export const getNavigation = state => state.navigation;
export const getDisplay = state => state.display;
export const getOpenModal = state => state.openModal;
export const getLatestChange = (state: ReduxState) =>
  state.entries.changes[state.entries.currentChangeIdx];

export const getNumUnscheduled = (state: ReduxState) =>
  state.entries.changes[state.entries.currentChangeIdx].unscheduled.length;
export const getSelectedId = (state: ReduxState) => state.entries.selectedId;

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
export const getDraggedContribs = createSelector(
  getEntries,
  getUnscheduled,
  (entries, contribs) => contribs.filter(c => entries.draggedIds.has(c.id))
);
export const getError = createSelector(
  getEntries,
  entries => entries.error
);

export const getNavbarMaxDays = createSelector(
  getNavigation,
  navigation => navigation.numDays
);
export const getNavbarOffset = createSelector(
  getNavigation,
  navigation => navigation.offset
);

export const getDisplayMode = createSelector(
  getDisplay,
  display => display.mode
);
export const showUnscheduled = createSelector(
  getDisplay,
  display => display.showUnscheduled
);
export const showAllTimeslots = createSelector(
  getDisplay,
  display => display.showAllTimeslots
);

export const getModalType = createSelector(
  getOpenModal,
  openModal => openModal.type
);
export const getModalEntry = createSelector(
  getOpenModal,
  openModal => openModal.entry
);

export const getPopupsEnabled = state => state.experimental.popupsEnabled;
