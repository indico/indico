// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSelector} from 'reselect';

import {applyChanges, appendSessionAttributes, getNumDays, mergeChanges} from './util';

export const getStaticData = state => state.staticData;
export const getEntries = state => state.entries;
export const getSessions = state => state.sessions;
export const getNavigation = state => state.navigation;
export const getDisplay = state => state.display;
export const getOpenModal = state => state.openModal;

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

export const getUpdatedEntries = createSelector(
  getEntries,
  entries => applyChanges(entries)
);
export const getBlocks = createSelector(
  getUpdatedEntries,
  getSessions,
  (entries, sessions) => appendSessionAttributes(entries.blocks, sessions)
);
export const getChildren = createSelector(
  getUpdatedEntries,
  getSessions,
  (entries, sessions) => appendSessionAttributes(entries.children, sessions)
);
export const getVisibleChildren = createSelector(
  getChildren,
  children => children.filter(c => !c.isPoster)
);
export const getUnscheduled = createSelector(
  getUpdatedEntries,
  getSessions,
  (entries, sessions) => appendSessionAttributes(entries.unscheduled, sessions)
);
export const getNumUnscheduled = createSelector(
  getUnscheduled,
  unscheduled => unscheduled.length
);
export const getVisibleEntries = createSelector(
  getBlocks,
  getVisibleChildren,
  (blocks, children) => [...blocks, ...children]
);
export const getSelectedId = createSelector(
  getEntries,
  entries => entries.selectedId
);
export const getSelectedEntry = createSelector(
  getVisibleEntries,
  getSelectedId,
  (entries, id) => id && entries.find(e => e.id === id)
);
export const canUndo = createSelector(
  getEntries,
  entries => entries.currentChangeIdx > 0
);
export const canRedo = createSelector(
  getEntries,
  entries => entries.currentChangeIdx < entries.changes.length
);
export const getMergedChanges = createSelector(
  getEntries,
  entries => mergeChanges(entries)
);
export const getDraggedContribs = createSelector(
  getEntries,
  getUnscheduled,
  (entries, contribs) => contribs.filter(c => entries.draggedIds.has(c.id))
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

export const getModalType = createSelector(
  getOpenModal,
  openModal => openModal.type
);
export const getModalEntry = createSelector(
  getOpenModal,
  openModal => openModal.entry
);
