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
import {
  preprocessSessionData,
  preprocessTimetableEntries,
  preprocessUnscheduledContributions,
} from './preprocess';
import {Entries, EntryType, isChildEntry, SidePanelView, ChildEntry, Entry} from './types';
import {setCurrentDateLocalStorage} from './utils';

export default {
  entries: (
    state: Entries = {
      draftEntry: null,
      entries: {},
      layoutOverrides: {},
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
        return {
          ...state,
          unscheduled: preprocessUnscheduledContributions(action.eventInfo.contributions),
          entries: preprocessTimetableEntries(action.data),
        };
      }
      case actions.CHANGE_ENTRY_LAYOUT: {
        // TODO get layout overrides from action
        const newLayoutOverrides = Object.fromEntries(
          action.entries.map(e => [
            e.id,
            {
              column: e.column,
              maxColumn: e.maxColumn,
            },
          ])
        );
        const newEntry: Entry = {
          ...state.entries[action.entry.id],
          startDt: action.entry.startDt,
        };
        if (isChildEntry(action.entry)) {
          (newEntry as ChildEntry).sessionBlockId = action.entry.sessionBlockId;
        }

        const updatedEntries: Record<string, Entry> = {
          [action.entry.id]: newEntry,
        };
        if (action.entry.type === EntryType.SessionBlock) {
          action.entry.children.forEach(entry => {
            updatedEntries[entry.id] = {...state.entries[entry.id], startDt: entry.startDt};
          });
        }
        const newEntries = {
          ...state.entries,
          ...updatedEntries,
        };
        const layoutOverrides = {...state.layoutOverrides, ...newLayoutOverrides};
        return {
          ...state,
          entries: newEntries,
          layoutOverrides,
        };
      }
      case actions.CREATE_ENTRY: {
        const {entry} = action;
        return {...state, entries: {...state.entries, [entry.id]: entry}};
      }
      case actions.UPDATE_UNSCHEDULED_ENTRY: {
        const {id, changes} = action;

        const updatedEntry = {...state.unscheduled.find(u => u.id === id), ...changes};
        const newUnscheduled = state.unscheduled.map(u => (u.id === id ? {...updatedEntry} : u));

        return {
          ...state,
          unscheduled: newUnscheduled,
        };
      }
      case actions.UPDATE_ENTRY: {
        const {entry, changes} = action;
        const deltaStartDt = moment(entry.startDt).diff(state.entries[entry.id].startDt, 'minutes');
        const updatedEntries = {
          [entry.id]: {...state.entries[entry.id], ...changes},
        };
        if (entry.type === EntryType.SessionBlock && deltaStartDt) {
          Object.values(state.entries)
            .filter(v => isChildEntry(v) && v.sessionBlockId === entry.id)
            .forEach(v => {
              updatedEntries[v.id] = {
                ...v,
                startDt: moment(v.startDt).add(deltaStartDt, 'minutes'),
              };
            });
        }
        return {...state, entries: {...state.entries, ...updatedEntries}};
      }
      case actions.RESIZE_ENTRY: {
        const {duration, entry} = action;
        return {
          ...state,
          entries: {
            ...state.entries,
            [entry.id]: {...state.entries[entry.id], duration},
          },
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
        return {
          ...state,
          entries: _.omit(state.entries, id),
        };
      }
      case actions.DELETE_BLOCK: {
        const {entry} = action;
        const newUnscheduled = Object.values(state.entries)
          .filter(
            x =>
              x.type === EntryType.Contribution && isChildEntry(x) && x.sessionBlockId === entry.id
          )
          .map(x => _.omit(x, ['startDt', 'sessionBlockId']));
        return {
          ...state,
          entries: _.omit(state.entries, [entry.id, ...newUnscheduled.map(c => c.id)]),
          unscheduled: [...state.unscheduled, ...newUnscheduled],
        };
      }
      case actions.SCHEDULE_ENTRY: {
        const {entry, layoutOverrides} = action;
        return {
          ...state,
          entries: {...state.entries, [entry.id]: entry},
          unscheduled: state.unscheduled.filter(c => c.id !== entry.id),
          layoutOverrides: {...state.layoutOverrides, ...layoutOverrides},
        };
      }
      case actions.UNSCHEDULE_ENTRY: {
        const {entry} = action;
        const unscheduledEntry = _.omit(state.entries[entry.id], ['startDt', 'sessionBlockId']);
        return {
          ...state,
          entries: _.omit(state.entries, entry.id),
          unscheduled: [...state.unscheduled, unscheduledEntry],
        };
      }
      case actions.DELETE_SESSION: {
        // Filter out all contribution entries linked to the session and also all its block entries
        const shouldKeepEntry = (entry: Entry) => {
          if (entry.type === EntryType.Contribution || entry.type === EntryType.SessionBlock) {
            return entry.sessionId !== action.sessionId;
          }
          return true;
        };
        const newEntries = Object.fromEntries(
          Object.entries(state.entries).filter(([, v]) => shouldKeepEntry(v))
        );
        // Pick all scheduled contribution entries that were linked to the session,
        // unschedule them and remove the session
        const newUnscheduled = Object.values(state.entries)
          .filter(
            x =>
              x.type === EntryType.Contribution &&
              isChildEntry(x) &&
              x.sessionId === action.sessionId
          )
          .map(x => ({..._.omit(x, ['startDt', 'sessionBlockId']), sessionId: null}));
        // Remove the deleted session from all existing unscheduled contributions
        const oldUnscheduled = state.unscheduled.map(contrib => ({
          ...contrib,
          sessionId: null,
        }));
        return {
          ...state,
          entries: newEntries,
          unscheduled: [...oldUnscheduled, ...newUnscheduled],
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
