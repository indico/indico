// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import {createSelector} from 'reselect';

import {ENTRY_COLORS_BY_BACKGROUND} from './colors';
import {BlockEntry, EntryType, ReduxState, Session} from './types';
import {
  DAY_SIZE,
  getDiffInDays,
  getDateKey,
  minutesToPixels,
  sortEntriesByStartDt,
  computeOverlappingEntryIds,
  flattenEntries,
} from './utils';

export const getStaticData = (state: ReduxState) => state.staticData;
export const getEntries = (state: ReduxState) => state.entries;
export const getDayEntries = (state: ReduxState) =>
  state.entries.changes[state.entries.currentChangeIdx].entries;
export const getSessions = (state: ReduxState) => state.sessions;
export const getNavigation = (state: ReduxState) => state.navigation;
export const getDisplay = (state: ReduxState) => state.display;
export const getLatestChange = (state: ReduxState) =>
  state.entries.changes[state.entries.currentChangeIdx];

// Get the selected entry ID
// You should not use this selector directly, use makeIsSelectedSelector instead
// to check if an entry is selected
export const getSelectedId = (state: ReduxState) => state.entries.selectedId;
// TODO(tomas): This is inefficient, but it'll go away when we refactor the whole redux state
export const getSelectedEntry = createSelector(
  [getDayEntries, getSelectedId],
  (entries, selectedId) => {
    if (!selectedId) {
      return null;
    }
    for (const dayEntries of Object.values(entries)) {
      for (const entry of dayEntries) {
        if (entry.id === selectedId) {
          return entry;
        }
        if (entry.type === EntryType.SessionBlock) {
          for (const child of entry.children) {
            if (child.id === selectedId) {
              return child;
            }
          }
        }
      }
    }
  }
);

export const getCurrentDate = (state: ReduxState) => state.navigation.currentDate;

export const makeIsSelectedSelector = () =>
  createSelector(
    [getSelectedId, (_state: ReduxState, id: string) => id],
    (selectedId, id) => selectedId === id
  );

export const getEventId = createSelector(
  getStaticData,
  staticData => {
    return staticData.eventId;
  }
);
export const getEventType = createSelector(
  getStaticData,
  staticData => staticData.eventType
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
  (startDt, endDt) => getDiffInDays(startDt, endDt) + 1
);
export const getSessionById = createSelector(
  getSessions,
  (_state: ReduxState, id: number) => id,
  (sessions, id) => sessions[id]
);

export const getCurrentDayEntries = createSelector(
  getDayEntries,
  getCurrentDate,
  (entries, currentDate) => entries[getDateKey(currentDate)]
);

export const getExpandedSessionBlockId = createSelector(
  getNavigation,
  navigation => navigation.expandedSessionBlockId
);

export const getExpandedSessionBlock = createSelector(
  getExpandedSessionBlockId,
  getCurrentDayEntries,
  (sessionBlockId, entries) =>
    entries.find(entry => entry.type === EntryType.SessionBlock && entry.id === sessionBlockId) ??
    null
);

export const getCurrentLimits = createSelector(
  getCurrentDate,
  getEventStartDt,
  getEventEndDt,
  getExpandedSessionBlock,
  (
    currentDate: Moment,
    startDt: Moment,
    endDt: Moment,
    sessionBlock: BlockEntry
  ): [number, number] => {
    const limits: [number, number] = [0, DAY_SIZE];

    if (sessionBlock) {
      startDt = moment(sessionBlock.startDt);
      endDt = moment(sessionBlock.startDt).add(sessionBlock.duration, 'minutes');
    }

    if (startDt.isSame(currentDate, 'day')) {
      limits[0] = minutesToPixels(moment.duration(startDt.format('HH:mm')).asMinutes());
    }

    if (endDt.isSame(currentDate, 'day')) {
      limits[1] = minutesToPixels(moment.duration(endDt.format('HH:mm')).asMinutes());
    }

    return limits;
  }
);

export const getCurrentEntries = createSelector(
  getCurrentDayEntries,
  getExpandedSessionBlock,
  (entries, sessionBlock: BlockEntry) => sessionBlock?.children ?? entries
);

export const getCurrentDayEntriesSorted = createSelector(
  getCurrentDayEntries,
  entries =>
    sortEntriesByStartDt(
      [...entries].map(e => {
        if (e.type === EntryType.SessionBlock && e?.children?.length) {
          return {
            ...e,
            children: sortEntriesByStartDt(e.children),
          } as BlockEntry;
        }
        return e;
      })
    )
);

export const getCurrentDayEntriesWithoutOverlap = createSelector(
  getCurrentDayEntriesSorted,
  entries => {
    const overlaps = computeOverlappingEntryIds(entries);

    return flattenEntries(entries)
      .map(e => e.id)
      .filter(id => !overlaps.has(id));
  }
);

export const getUnscheduled = createSelector(
  getLatestChange,
  getSessions,
  (entries, sessions) => appendSessionAttributes(entries.unscheduled, sessions)
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

export const showUnscheduled = createSelector(
  getDisplay,
  display => display.showUnscheduled
);

export const getDefaultContribDurationMinutes = createSelector(
  getStaticData,
  getSessions,
  getExpandedSessionBlock,
  (staticData, sessions, expandedSessionBlock) => {
    const session = sessions[expandedSessionBlock?.sessionId];
    return session?.defaultContribDurationMinutes || staticData.defaultContribDurationMinutes;
  }
);

export const getEventLocationParent = createSelector(
  getStaticData,
  staticData => staticData.eventLocationParent
);

// Navigation state
export const getIsExpanded = createSelector(
  getNavigation,
  navigation => navigation.isExpanded
);

function appendSessionAttributes(entries: any[], sessions: Record<string, Session>) {
  return entries.map(e => {
    if (!e.sessionId) {
      return e;
    }
    const session = sessions[e.sessionId];
    const isPoster = session.isPoster;
    const colors = ENTRY_COLORS_BY_BACKGROUND[session.colors.backgroundColor];
    return {...e, isPoster, colors};
  });
}
