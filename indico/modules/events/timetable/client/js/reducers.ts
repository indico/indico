// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {Moment} from 'moment';

import * as actions from './actions';
import {layout, layoutDays} from './layout';
import {changeSessionColor, changeBreakColor} from './operations';
import {preprocessSessionData, preprocessTimetableEntries} from './preprocess';
import {DayEntries} from './types';
import {setCurrentDateLocalStorage} from './utils';

interface Change {
  change: any;
  entries: DayEntries;
  unscheduled: any[];
}

interface Entries {
  draftEntry: any | null;
  changes: Change[];
  currentChangeIdx: number;
  selectedId: number | null;
  draggedIds: Set<number>;
  error: string | null;
}

export interface ReduxState {
  entries: Entries;
  sessions: any[];
  navigation: {numDays: number; currentDate: Moment; isExpanded: boolean};
  display: {showUnscheduled: boolean};
}

export default {
  entries: (
    state: Entries = {
      draftEntry: null,
      changes: [],
      currentChangeIdx: 0,
      selectedId: null,
      draggedIds: new Set(),
      error: null,
    },
    action: actions.Action
  ) => {
    switch (action.type) {
      case actions.SET_DRAFT_ENTRY:
        return {...state, draftEntry: action.data};
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
      case actions.UPDATE_ENTRY: {
        const {
          entry,
          entryType,
          entry: {startDt},
        } = action;
        const newEntries = {...state.changes[state.currentChangeIdx].entries};

        const dayKey = moment(startDt).format('YYYYMMDD');
        const dayEntries = newEntries[dayKey];

        const editedIndex = dayEntries.findIndex(e => {
          return e.id === entry.id && e.type === entryType;
        });

        newEntries[dayKey][editedIndex] = entry;

        // TODO: (Ajob) make sure to edit entry first
        newEntries[dayKey] = layout([...dayEntries]);

        return {
          ...state,
          currentChangeIdx: state.currentChangeIdx + 1,
          changes: [
            ...state.changes.slice(0, state.currentChangeIdx + 1),
            {
              entries: newEntries,
              change: 'update',
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
      case actions.DESELECT_ENTRY:
        return {...state, selectedId: null};
      // return {...state};
      case actions.DELETE_BREAK: {
        const {id} = action.entry;
        if ('parentId' in action.entry) {
          const parentId = action.entry.parentId;
          const newEntries = layoutDays(
            Object.fromEntries(
              Object.entries(state.changes[state.currentChangeIdx].entries).map(
                ([day, dayEntries]) => [
                  day,
                  dayEntries.map(e => {
                    if (e.type === 'block' && e.id === parentId) {
                      return {
                        ...e,
                        children: e.children.filter(child => child.id !== id),
                      };
                    }
                    return e;
                  }),
                ]
              )
            )
          );
          return {
            ...state,
            currentChangeIdx: state.currentChangeIdx + 1,
            changes: [
              ...state.changes.slice(0, state.currentChangeIdx + 1),
              {
                entries: newEntries,
                change: 'delete',
                unscheduled: state.changes[state.currentChangeIdx].unscheduled,
              },
            ],
          };
        } else {
          const newEntries = layoutDays(
            Object.fromEntries(
              Object.entries(state.changes[state.currentChangeIdx].entries).map(
                ([day, dayEntries]) => [day, dayEntries.filter(e => e.id !== id)]
              )
            )
          );
          return {
            ...state,
            currentChangeIdx: state.currentChangeIdx + 1,
            changes: [
              ...state.changes.slice(0, state.currentChangeIdx + 1),
              {
                entries: newEntries,
                change: 'delete',
                unscheduled: state.changes[state.currentChangeIdx].unscheduled,
              },
            ],
          };
        }
      }
      case actions.DELETE_BLOCK: {
        const {id} = action.entry;
        let block = null;
        for (const dayEntries of Object.values(state.changes[state.currentChangeIdx].entries)) {
          block = dayEntries.find(e => e.id === id);
          if (block) {
            break;
          }
        }

        if (!block) {
          return state;
        }

        const contribs = block.children
          .filter(e => e.type === 'contrib')
          .map(({startDt, ...rest}) => rest);
        const newEntries = layoutDays(
          Object.fromEntries(
            Object.entries(state.changes[state.currentChangeIdx].entries).map(
              ([day, dayEntries]) => [day, dayEntries.filter(e => e.id !== id)]
            )
          )
        );

        return {
          ...state,
          currentChangeIdx: state.currentChangeIdx + 1,
          changes: [
            ...state.changes.slice(0, state.currentChangeIdx + 1),
            {
              entries: newEntries,
              change: 'delete',
              unscheduled: [state.changes[state.currentChangeIdx].unscheduled, ...contribs],
            },
          ],
        };
      }
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
      case actions.UNSCHEDULE_ENTRY: {
        const {id} = action.entry;
        if ('parentId' in action.entry) {
          const parentId = action.entry.parentId;
          const newEntries = layoutDays(
            Object.fromEntries(
              Object.entries(state.changes[state.currentChangeIdx].entries).map(
                ([day, dayEntries]) => [
                  day,
                  dayEntries.map(e => {
                    if (e.type === 'block' && e.id === parentId) {
                      return {
                        ...e,
                        children: e.children.filter(child => child.id !== id),
                      };
                    }
                    return e;
                  }),
                ]
              )
            )
          );
          return {
            ...state,
            currentChangeIdx: state.currentChangeIdx + 1,
            changes: [
              ...state.changes.slice(0, state.currentChangeIdx + 1),
              {
                entries: newEntries,
                change: 'unschedule',
                unscheduled: [...state.changes[state.currentChangeIdx].unscheduled, action.entry],
              },
            ],
          };
        } else {
          const newEntries = layoutDays(
            Object.fromEntries(
              Object.entries(state.changes[state.currentChangeIdx].entries).map(
                ([day, dayEntries]) => [day, dayEntries.filter(e => e.id !== id)]
              )
            )
          );
          return {
            ...state,
            currentChangeIdx: state.currentChangeIdx + 1,
            changes: [
              ...state.changes.slice(0, state.currentChangeIdx + 1),
              {
                entries: newEntries,
                change: 'unschedule',
                unscheduled: [...state.changes[state.currentChangeIdx].unscheduled, action.entry],
              },
            ],
          };
        }
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
  navigation: (state, action) => {
    state = {isExpanded: false, ...state};
    switch (action.type) {
      case actions.SCROLL_NAVBAR:
        return {...state, offset: action.offset};
      case actions.SET_CURRENT_DATE:
        setCurrentDateLocalStorage(action.date, action.eventId);
        return {...state, currentDate: action.date};
      case actions.TOGGLE_EXPAND:
        return {...state, isExpanded: !state.isExpanded};
      case actions.TOGGLE_DRAFT:
        return {...state, isDraft: !state.isDraft};
      default:
        return state;
    }
  },
  display: (state = {showUnscheduled: false}, action) => {
    switch (action.type) {
      case actions.TOGGLE_SHOW_UNSCHEDULED:
        return {...state, showUnscheduled: !state.showUnscheduled};
      default:
        return state;
    }
  },
};
