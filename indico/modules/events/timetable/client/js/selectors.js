// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSelector} from 'reselect';

import {applyChanges, getNumDays} from './util';

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

export const getUpdatedEntries = createSelector(
  getEntries,
  entries => applyChanges(entries)
);
export const getBlocks = createSelector(
  getUpdatedEntries,
  entries => entries.blocks
);
export const getChildren = createSelector(
  getUpdatedEntries,
  entries => entries.children
);
export const getAllEntries = createSelector(
  getBlocks,
  getChildren,
  (blocks, children) => [...blocks, ...children]
);
export const getSelectedId = createSelector(
  getEntries,
  entries => entries.selectedId
);
export const getSelectedEntry = createSelector(
  getAllEntries,
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

export const getNavbarMaxDays = createSelector(
  getNavigation,
  navigation => navigation.numDays
);
export const getNavbarOffset = createSelector(
  getNavigation,
  navigation => navigation.offset
);
