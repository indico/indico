// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSlice, PayloadAction} from '@reduxjs/toolkit';
import moment from 'moment';

import {layoutDays, layout} from './layout';
import * as operations from './operations';
import {EventInfo, preprocessTimetableEntries, TimetableData} from './preprocess';
import {DayEntries, Entry, UnscheduledContrib} from './types';

interface Change {
  change?: any;
  entries: DayEntries;
  unscheduled: any[];
}

interface EntriesState {
  changes: Change[];
  currentChangeIdx: number;
  selectedId: number | null;
  draggedIds: Set<number>;
  error: string | null;
}

const initialState: EntriesState = {
  changes: [],
  currentChangeIdx: 0,
  selectedId: null,
  draggedIds: new Set(),
  error: null,
};

export const entriesSlice = createSlice({
  name: 'entries',
  initialState,
  reducers: {
    setTimetableData: (
      state,
      action: PayloadAction<{data: TimetableData; eventInfo: EventInfo}>
    ) => {
      const {dayEntries, unscheduled} = preprocessTimetableEntries(
        action.payload.data,
        action.payload.eventInfo
      );
      state.changes = [{entries: layoutDays(dayEntries), unscheduled}];
    },
    moveEntry: (state, action: PayloadAction<{date: string; entries: Entry[]}>) => {
      const date = action.payload.date;
      const newEntries = Object.fromEntries(
        Object.entries(state.changes[state.currentChangeIdx].entries).map(([day, dayEntries]) => [
          day,
          day === date ? action.payload.entries : dayEntries,
        ])
      );
      state.currentChangeIdx++;
      state.changes = [
        ...state.changes.slice(0, state.currentChangeIdx),
        {
          entries: newEntries,
          change: 'move',
          unscheduled: state.changes[state.currentChangeIdx - 1].unscheduled,
        },
      ];
    },
    resizeEntry: (
      state,
      action: PayloadAction<{date: string; id: number; duration: number; parentId?: number}>
    ) => {
      const {date, id, parentId, duration} = action.payload;
      let newDayEntries: Entry[];
      if (parentId !== undefined) {
        const parent = state.changes[state.currentChangeIdx].entries[date].find(
          (e: Entry) => e.id === parentId
        );
        if (!parent) {
          return;
        }
        newDayEntries = layout(
          state.changes[state.currentChangeIdx].entries[date].map(entry => {
            if (entry.type === 'block' && entry.id === parentId) {
              return {
                ...entry,
                children: entry.children.map(child => {
                  if (child.id === id) {
                    return {
                      ...child,
                      duration: moment(entry.startDt)
                        .add(duration, 'minutes')
                        .isBefore(moment(child.startDt).add(entry.duration, 'minutes'))
                        ? duration
                        : entry.duration,
                    };
                  }
                  return child;
                }),
              };
            }
            return entry;
          })
        );
      } else {
        const entry = state.changes[state.currentChangeIdx].entries[date].find(
          (e: Entry) => e.id === id
        );
        if (!entry) {
          return;
        }
        newDayEntries = layout(
          state.changes[state.currentChangeIdx].entries[date].map((e: Entry) =>
            e.id === id ? {...e, duration} : e
          )
        );
      }
      const newEntries = Object.fromEntries(
        Object.entries(state.changes[state.currentChangeIdx].entries).map(([day, dayEntries]) => [
          day,
          day === date ? newDayEntries : dayEntries,
        ])
      );
      state.currentChangeIdx++;
      state.changes = [
        ...state.changes.slice(0, state.currentChangeIdx),
        {
          entries: newEntries,
          change: 'resize',
          unscheduled: state.changes[state.currentChangeIdx - 1].unscheduled,
        },
      ];
    },
    selectEntry: (state, action: PayloadAction<number | null>) => {
      state.selectedId = action.payload;
    },
    dragEntry: (state, action: PayloadAction<number>) => {
      state.draggedIds.add(action.payload);
    },
    deleteEntry: (state, action: PayloadAction<Entry>) => {
      state = {
        ...state,
        ...operations.deleteEntry(state, action.payload),
        selectedId: (action.payload || {}).id === state.selectedId ? null : state.selectedId,
      };
      // TODO test this
    },
    dragUnscheduledContribs: (state, action: PayloadAction<number[]>) => {
      state.draggedIds = new Set(action.payload);
    },
    dropUnscheduledContribs: (
      state,
      action: PayloadAction<{contribs: UnscheduledContrib[]; args: any}>
    ) => {
      state = {
        ...state,
        ...operations.dropUnscheduledContribs(state, action.payload.contribs, action.payload.args),
        draggedIds: new Set(),
      };
      // TODO test this
    },
    scheduleEntry: (
      state,
      action: PayloadAction<{date: string; entries: Entry[]; unscheduled: UnscheduledContrib[]}>
    ) => {
      const date = action.payload.date;
      const newEntries = Object.fromEntries(
        Object.entries(state.changes[state.currentChangeIdx].entries).map(([day, dayEntries]) => [
          day,
          day === date ? action.payload.entries : dayEntries,
        ])
      );
      state.currentChangeIdx++;
      state.changes = [
        ...state.changes.slice(0, state.currentChangeIdx),
        {
          entries: newEntries,
          change: 'resize',
          unscheduled: action.payload.unscheduled,
        },
      ];
    },
    scheduleContribs: (state, action: PayloadAction<{contribIds: number[]; gap: number}>) => {
      state = {
        ...state,
        ...operations.scheduleContribs(state, action.payload.contribIds, action.payload.gap),
        draggedIds: new Set(),
      };
      // TODO test this
    },
    changeBreakColor: (state, action: PayloadAction<string>) => {
      state = {...state, ...operations.changeBreakColor(state, action.payload)};
    },
    undoChange: state => {
      state.currentChangeIdx = Math.max(0, state.currentChangeIdx - 1);
    },
    redoChange: state => {
      state.currentChangeIdx = Math.min(state.changes.length - 1, state.currentChangeIdx + 1);
    },
    dismissError: state => {
      state.error = null;
    },
  },
});

export const {
  setTimetableData,
  moveEntry,
  resizeEntry,
  selectEntry,
  dragEntry,
  deleteEntry,
  dragUnscheduledContribs,
  scheduleEntry,
  scheduleContribs,
  changeBreakColor,
  undoChange,
  redoChange,
  dismissError,
} = entriesSlice.actions;

export default entriesSlice.reducer;
