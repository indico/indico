// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';

import * as actions from './actions';
import {Action} from './actions';
import {layout, layoutDays} from './layout';
import {preprocessSessionData, preprocessTimetableEntries} from './preprocess';
import {BlockEntry, Entries, EntryType, isChildEntry, SidePanelView} from './types';
import {getDateKey, getEntryUniqueId, setCurrentDateLocalStorage, shiftEntries} from './utils';

export default {
  entries: (
    state: Entries = {
      draftEntry: null,
      entries: {},
      unscheduled: [],
      selectedId: null,
      draggedIds: new Set(),
    },
    action: actions.Action
  ) => {
    switch (action.type) {
      case actions.SET_DRAFT_ENTRY:
        return {...state, draftEntry: action.data};
      case actions.SET_TIMETABLE_DATA: {
        const {dayEntries, unscheduled} = preprocessTimetableEntries(action.data, action.eventInfo);
        return {...state, entries: layoutDays(dayEntries), unscheduled};
      }
      case actions.CHANGE_ENTRY_LAYOUT: {
        const date = action.date;
        const newEntries = Object.fromEntries(
          Object.entries(state.entries).map(([day, dayEntries]) => [
            day,
            day === date ? action.entries : dayEntries,
          ])
        );
        return {
          ...state,
          entries: newEntries,
        };
      }
      case actions.CREATE_ENTRY: {
        const {
          entry,
          entry: {startDt},
        } = action;
        const newEntries = {...state.entries};

        const dayKey = moment(startDt).format('YYYYMMDD');
        const dayEntries = newEntries[dayKey];

        if (isChildEntry(entry)) {
          const newDayEntries = newEntries[dayKey].map(e => {
            if (e.id === entry.sessionBlockId && e.type === EntryType.SessionBlock) {
              return {
                ...e,
                children: [...e.children, entry],
              };
            }
            return e;
          });
          newEntries[dayKey] = layout(newDayEntries);
        } else {
          newEntries[dayKey] = layout([...dayEntries, entry]);
        }

        return {
          ...state,
          entries: newEntries,
        };
      }
      case actions.UPDATE_UNSCHEDULED_ENTRY: {
        const {entry, entryType} = action;

        const uid = getEntryUniqueId(entryType, entry.objId);
        const updatedUnscheduled = state.unscheduled.map(u => {
          return u.id === uid ? entry : u;
        });

        return {
          ...state,
          unscheduled: updatedUnscheduled,
        };
      }
      case actions.SET_ENTRY_ATTACHMENTS: {
        const {id, attachments} = action;
        const newEntries = {...state.entries};
        const flatEntries = Object.values(newEntries)
          .flat()
          .map(e => [e, ...(e.type === EntryType.SessionBlock ? e.children : [])])
          .flat();
        const entry = flatEntries.find(e => e.id === id);
        if (!entry || entry.type === EntryType.Break) {
          return state;
        }

        const dateKey = getDateKey(entry.startDt);
        const dayEntries = newEntries[dateKey];
        if (isChildEntry(entry)) {
          const parentEntry = dayEntries.find(dayEntry => dayEntry.id === entry.sessionBlockId);
          if (parentEntry === undefined || parentEntry.type !== EntryType.SessionBlock) {
            return state;
          }
          newEntries[dateKey] = [
            ...dayEntries.filter(dayEntry => dayEntry.id !== parentEntry.id),
            {
              ...parentEntry,
              children: [
                ...parentEntry.children.filter(childEntry => childEntry.id !== id),
                {
                  ...entry,
                  attachments,
                },
              ],
            },
          ];
        } else if (entry.type === EntryType.Contribution) {
          newEntries[dateKey] = [
            ...dayEntries.filter(dayEntry => dayEntry.id !== id),
            {...entry, attachments},
          ];
        } else {
          // attachments are linked to sessions, not session blocks, so we must update every
          // session block that matches this sessionId
          for (const key of Object.keys(newEntries)) {
            newEntries[key] = newEntries[key].map(dayEntry =>
              dayEntry.type === EntryType.SessionBlock && dayEntry.sessionId === entry.sessionId
                ? {...dayEntry, attachments}
                : dayEntry
            );
          }
        }

        return {
          ...state,
          entries: newEntries,
        };
      }
      case actions.UPDATE_ENTRY: {
        const {
          entry,
          entryType,
          entry: {startDt},
          currentDay,
        } = action;
        const newEntries = {...state.entries};
        const currentDayKey = currentDay;
        const dayEntries = [...newEntries[currentDayKey]];
        const newDayKey = getDateKey(startDt);

        if (!isChildEntry(entry) && entry.type === EntryType.SessionBlock) {
          const oldEntry = dayEntries.find(e => e.id === entry.id);
          const deltaStartDt = moment(entry.startDt).diff(oldEntry.startDt, 'minutes');
          entry.children = shiftEntries(entry.children, deltaStartDt);
        }

        if (currentDayKey !== newDayKey) {
          newEntries[newDayKey] = layout([...newEntries[newDayKey], entry]);
          newEntries[currentDayKey] = layout([...dayEntries.filter(e => e.id !== entry.id)]);
        } else {
          newEntries[newDayKey] = layout(
            newEntries[newDayKey].map(e => {
              if (isChildEntry(entry) && entry.sessionBlockId === e.id) {
                if (e.type !== EntryType.SessionBlock) {
                  return e;
                }
                return {
                  ...e,
                  children: e.children.map(child => (child.id === entry.id ? entry : child)),
                };
              }
              return e.id === entry.id && e.type === entryType ? entry : e;
            })
          );
        }

        return {
          ...state,
          entries: newEntries,
        };
      }
      case actions.RESIZE_ENTRY: {
        const {date, duration, entry} = action;
        let newDayEntries;

        if (isChildEntry(entry)) {
          const sessionBlockId = entry.sessionBlockId;
          const parent = state.entries[date].find(e => e.id === sessionBlockId);
          if (!parent) {
            return state;
          }
          newDayEntries = layout(
            state.entries[date].map(e => {
              if (e.type === EntryType.SessionBlock && e.id === sessionBlockId) {
                return {
                  ...e,
                  children: e.children.map(child => {
                    if (child.id === entry.id) {
                      return {
                        ...child,
                        duration: moment(e.startDt)
                          .add(duration, 'minutes')
                          .isBefore(moment(child.startDt).add(e.duration, 'minutes'))
                          ? duration
                          : e.duration,
                      };
                    }
                    return child;
                  }),
                };
              }
              return e;
            })
          );
        } else {
          newDayEntries = layout(
            state.entries[date].map(e => (e.id === entry.id ? {...e, duration} : e))
          );
        }
        const newEntries = Object.fromEntries(
          Object.entries(state.entries).map(([day, dayEntries]) => [
            day,
            day === date ? newDayEntries : dayEntries,
          ])
        );
        return {
          ...state,
          entries: newEntries,
        };
      }
      case actions.SELECT_ENTRY:
        return {...state, selectedId: action.id};
      case actions.DESELECT_ENTRY:
        return {...state, selectedId: null};
      case actions.DELETE_UNSCHEDULED_CONTRIB: {
        const {id} = action;
        return {
          ...state,
          unscheduled: state.unscheduled.filter(e => e.id !== id),
        };
      }
      case actions.ADD_UNSCHEDULED_CONTRIB: {
        const {entry} = action;
        return {
          ...state,
          unscheduled: [entry, ...state.unscheduled],
        };
      }
      case actions.DELETE_BREAK: {
        const {entry} = action;
        const {id} = entry;
        if (isChildEntry(entry)) {
          const sessionBlockId = entry.sessionBlockId;
          const newEntries = layoutDays(
            Object.fromEntries(
              Object.entries(state.entries).map(([day, dayEntries]) => [
                day,
                dayEntries.map(e => {
                  if (e.type === EntryType.SessionBlock && e.id === sessionBlockId) {
                    return {
                      ...e,
                      children: e.children.filter(child => child.id !== id),
                    };
                  }
                  return e;
                }),
              ])
            )
          );
          return {
            ...state,
            entries: newEntries,
          };
        } else {
          const newEntries = layoutDays(
            Object.fromEntries(
              Object.entries(state.entries).map(([day, dayEntries]) => [
                day,
                dayEntries.filter(e => e.id !== id),
              ])
            )
          );
          return {
            ...state,
            entries: newEntries,
          };
        }
      }
      case actions.DELETE_BLOCK: {
        const {id} = action.entry;
        let block = null;
        for (const dayEntries of Object.values(state.entries)) {
          block = dayEntries.find(e => e.id === id);
          if (block) {
            break;
          }
        }

        if (!block) {
          return state;
        }

        const contribs = (block as BlockEntry).children
          .filter(e => e.type === 'contrib')
          .map(({startDt, ...rest}) => rest);
        const newEntries = layoutDays(
          Object.fromEntries(
            Object.entries(state.entries).map(([day, dayEntries]) => [
              day,
              dayEntries.filter(e => e.id !== id),
            ])
          )
        );

        return {
          ...state,
          entries: newEntries,
          unscheduled: [...state.unscheduled, ...contribs],
        };
      }
      case actions.SCHEDULE_ENTRY: {
        const date = action.date;
        const newEntries = Object.fromEntries(
          Object.entries(state.entries).map(([day, dayEntries]) => [
            day,
            day === date ? action.entries : dayEntries,
          ])
        );
        return {
          ...state,
          entries: newEntries,
          unscheduled: action.unscheduled,
        };
      }
      case actions.UNSCHEDULE_ENTRY: {
        const {entry} = action;
        const {id} = entry;
        if (isChildEntry(entry)) {
          const sessionBlockId = entry.sessionBlockId;
          const newEntries = layoutDays(
            Object.fromEntries(
              Object.entries(state.entries).map(([day, dayEntries]) => [
                day,
                dayEntries.map(e => {
                  if (e.type === EntryType.SessionBlock && e.id === sessionBlockId) {
                    return {
                      ...e,
                      children: e.children.filter(child => child.id !== id),
                    };
                  }
                  return e;
                }),
              ])
            )
          );
          return {
            ...state,
            entries: newEntries,
            unscheduled: [...state.unscheduled, action.entry],
          };
        } else {
          const newEntries = layoutDays(
            Object.fromEntries(
              Object.entries(state.entries).map(([day, dayEntries]) => [
                day,
                dayEntries.filter(e => e.id !== id),
              ])
            )
          );
          return {
            ...state,
            entries: newEntries,
            unscheduled: [...state.unscheduled, action.entry],
          };
        }
      }
      case actions.DELETE_SESSION: {
        // Remove all entries belonging to the session being deleted &
        // unschedule all contributions linked to it
        const {sessionId} = action;
        const contribsToUnschedule = [];

        const newEntries = Object.fromEntries(
          Object.entries(state.entries).map(([day, dayEntries]) => [
            day,
            dayEntries.filter(e => {
              if (e.type === EntryType.SessionBlock && e.sessionId === sessionId) {
                for (const child of e.children) {
                  if (child.type === EntryType.Contribution) {
                    contribsToUnschedule.push({
                      ...child,
                      sessionId: null,
                      sessionBlockId: null,
                    });
                  }
                }
              }

              return e.sessionId !== sessionId;
            }),
          ])
        );

        const newUnscheduled = state.unscheduled
          .map(u =>
            u.sessionId === sessionId
              ? {
                  ...u,
                  sessionId: null,
                }
              : u
          )
          .concat(contribsToUnschedule);

        return {
          ...state,
          entries: newEntries,
          unscheduled: newUnscheduled,
        };
      }
      default:
        return state;
    }
  },
  sessions: (state = [], action: Action) => {
    switch (action.type) {
      case actions.SET_SESSION_DATA:
        return preprocessSessionData(action.data);
      case actions.EDIT_SESSION:
        return {
          ...state,
          ...{[action.session.id]: {...action.session}},
        };
      case actions.DELETE_SESSION: {
        return _.omit(state, action.sessionId);
      }
      case actions.CREATE_SESSION:
        return {
          ...state,
          ...{[action.session.id]: {...action.session, isPoster: false}},
        };
      default:
        return state;
    }
  },
  navigation: (state: any, action: Action) => {
    state = {isExpanded: false, ...state};
    switch (action.type) {
      case actions.SET_CURRENT_DATE:
        setCurrentDateLocalStorage(action.date, action.eventId);
        return {...state, currentDate: action.date};
      case actions.TOGGLE_EXPAND:
        return {...state, isExpanded: !state.isExpanded};
      case actions.TOGGLE_DRAFT:
        return {...state, isDraft: !state.isDraft};
      case actions.SET_EXPANDED_SESSION_BLOCK_ID:
        return {...state, expandedSessionBlockId: action.sessionBlockId};
      default:
        return state;
    }
  },
  display: (state = {activePanel: SidePanelView.None}, action: Action) => {
    switch (action.type) {
      case actions.SET_ACTIVE_PANEL:
        return {
          ...state,
          activePanel: action.panel,
        };

      default:
        return state;
    }
  },
};
