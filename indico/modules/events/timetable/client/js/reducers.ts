// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';

import * as actions from './actions';
import {layout, layoutDays} from './layout';
import {
  deleteEntry,
  scheduleContribs,
  resizeWindow,
  changeSessionColor,
  changeBreakColor,
  dropUnscheduledContribs,
} from './operations';
import {preprocessSessionData, preprocessTimetableEntries} from './preprocess';
import {DayEntries} from './types';

interface Change {
  change: any;
  entries: DayEntries;
  unscheduled: any[];
}

interface Entries {
  changes: Change[];
  currentChangeIdx: number;
  selectedId: number | null;
  draggedIds: Set<number>;
  error: string | null;
}

export interface ReduxState {
  entries: Entries;
  sessions: any[];
  navigation: {numDays: number; offset: number};
  display: {mode: string; showUnscheduled: boolean};
  openModal: {type: string | null; entry: any};
  experimental: {popupsEnabled: boolean};
}

export default {
  entries: (
    state: Entries = {
      changes: [],
      currentChangeIdx: 0,
      selectedId: null,
      draggedIds: new Set(),
      error: null,
    },
    action: actions.Action
  ) => {
    switch (action.type) {
      case actions.SET_TIMETABLE_DATA: {
        const {dayEntries, unscheduled} = preprocessTimetableEntries(action.data, action.eventInfo);
        return {...state, changes: [{entries: layoutDays(dayEntries), unscheduled}]};
      }
      case actions.MOVE_ENTRY: {
        const date = action.date;
        const newEntries = Object.fromEntries(
          Object.entries(state.changes[state.currentChangeIdx].entries).map(([day, dayEntries]) => [
            day,
            day === date ? action.entries : dayEntries,
          ])
        );
        return {
          ...state,
          currentChangeIdx: state.currentChangeIdx + 1,
          changes: [
            ...state.changes.slice(0, state.currentChangeIdx + 1),
            {
              entries: newEntries,
              change: 'move',
              unscheduled: state.changes[state.currentChangeIdx].unscheduled,
            },
          ],
        };
      }
      case actions.CREATE_ENTRY: {
        const {
          entry,
          entry: {startDt},
        } = action;
        const newEntries = {...state.changes[state.currentChangeIdx].entries};

        const dayKey = moment(startDt).format('YYYYMMDD');
        const dayEntries = newEntries[dayKey];

        newEntries[dayKey] = layout([...dayEntries, entry]);

        return {
          ...state,
          currentChangeIdx: state.currentChangeIdx + 1,
          changes: [
            ...state.changes.slice(0, state.currentChangeIdx + 1),
            {
              entries: newEntries,
              change: 'create',
              unscheduled: state.changes[state.currentChangeIdx].unscheduled,
            },
          ],
        };
      }
      case actions.RESIZE_ENTRY: {
        const {date, id, parentId, duration} = action;
        let newDayEntries;
        if (parentId !== undefined) {
          const parent = state.changes[state.currentChangeIdx].entries[date].find(
            e => e.id === parentId
          );
          if (!parent) {
            return state;
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
          const entry = state.changes[state.currentChangeIdx].entries[date].find(e => e.id === id);
          if (!entry) {
            return state;
          }
          newDayEntries = layout(
            state.changes[state.currentChangeIdx].entries[date].map(e =>
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
        return {
          ...state,
          currentChangeIdx: state.currentChangeIdx + 1,
          changes: [
            ...state.changes.slice(0, state.currentChangeIdx + 1),
            {
              entries: newEntries,
              change: 'resize',
              unscheduled: state.changes[state.currentChangeIdx].unscheduled,
            },
          ],
        };
      }
      case actions.SELECT_ENTRY:
        return {...state, selectedId: action.id};
      // return {...state};
      case actions.DELETE_ENTRY:
        return {
          ...state,
          ...deleteEntry(state, action.entry),
          selectedId: (action.entry || {}).id === state.selectedId ? null : state.selectedId,
        };
      case actions.DRAG_UNSCHEDULED_CONTRIBS:
        return {...state, draggedIds: action.contribIds};
      case actions.DROP_UNSCHEDULED_CONTRIBS:
        return {
          ...state,
          ...dropUnscheduledContribs(state, action.contribs, action.args),
          draggedIds: new Set(),
        };
      case actions.SCHEDULE_ENTRY: {
        const date = action.date;
        const newEntries = Object.fromEntries(
          Object.entries(state.changes[state.currentChangeIdx].entries).map(([day, dayEntries]) => [
            day,
            day === date ? action.entries : dayEntries,
          ])
        );
        return {
          ...state,
          currentChangeIdx: state.currentChangeIdx + 1,
          changes: [
            ...state.changes.slice(0, state.currentChangeIdx + 1),
            {
              entries: newEntries,
              change: 'resize',
              unscheduled: action.unscheduled,
            },
          ],
        };
      }
      case actions.SCHEDULE_CONTRIBS: {
        const [entries, unscheduled] = scheduleContribs(
          state,
          action.contribs,
          action.gap,
          action.startDt,
          action.dt
        );
        const date = action.startDt.format('YYYYMMDD');
        const newEntries = Object.fromEntries(
          Object.entries(state.changes[state.currentChangeIdx].entries).map(([day, dayEntries]) => [
            day,
            day === date ? entries : dayEntries,
          ])
        );
        return {
          ...state,
          currentChangeIdx: state.currentChangeIdx + 1,
          changes: [
            ...state.changes.slice(0, state.currentChangeIdx + 1),
            {
              entries: newEntries,
              change: 'schedule',
              unscheduled,
            },
          ],
          draggedIds: new Set(),
        };
      }
      case actions.CHANGE_COLOR:
        return action.sessionId ? state : {...state, ...changeBreakColor(state, action.color)};
      case actions.UNDO_CHANGE:
        return {
          ...state,
          currentChangeIdx: Math.max(0, state.currentChangeIdx - 1),
        };
      case actions.REDO_CHANGE:
        return {
          ...state,
          currentChangeIdx: Math.min(state.changes.length - 1, state.currentChangeIdx + 1),
        };
      case actions.DISMISS_ERROR:
        return {...state, error: null};
      default:
        return state;
    }
  },
  sessions: (state = [], action) => {
    switch (action.type) {
      case actions.SET_SESSION_DATA:
        return preprocessSessionData(action.data);
      case actions.ADD_SESSION_DATA:
        return preprocessSessionData({
          ...Object.fromEntries(Object.entries(state)),
          [action.data.id]: {...action.data, isPoster: false},
        });
      case actions.CHANGE_COLOR:
        return action.sessionId ? changeSessionColor(state, action.sessionId, action.color) : state;
      default:
        return state;
    }
  },
  navigation: (state = {numDays: 2, offset: 0}, action) => {
    switch (action.type) {
      case actions.SCROLL_NAVBAR:
        return {...state, offset: action.offset};
      case actions.RESIZE_WINDOW:
        return resizeWindow(state, action);
      default:
        return state;
    }
  },
  display: (state = {mode: 'compact', showUnscheduled: false, showAllTimeslots: true}, action) => {
    switch (action.type) {
      case actions.SET_DISPLAY_MODE:
        return {...state, mode: action.mode};
      case actions.TOGGLE_SHOW_UNSCHEDULED:
        return {...state, showUnscheduled: !state.showUnscheduled};
      case actions.TOGGLE_SHOW_ALL_TIMESLOTS:
        return {...state, showAllTimeslots: !state.showAllTimeslots};
      default:
        return state;
    }
  },
  openModal: (state = {type: null, entry: null}, action) => {
    switch (action.type) {
      case actions.ADD_ENTRY:
        return {type: action.entryType, entry: null};
      case actions.EDIT_ENTRY:
        return {type: action.entryType, entry: action.entry};
      case actions.CLOSE_MODAL:
        return {type: null, entry: null};
      default:
        return state;
    }
  },
  experimental: (state = {popupsEnabled: true}, action) => {
    switch (action.type) {
      case actions.EXPERIMENTAL_TOGGLE_POPUPS:
        return {popupsEnabled: !state.popupsEnabled};
      default:
        return state;
    }
  },
};
