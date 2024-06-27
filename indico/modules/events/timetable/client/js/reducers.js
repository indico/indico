// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

import * as actions from './actions';
import {
  resizeEntry,
  deleteEntry,
  scheduleContribs,
  preprocessEntries,
  resizeWindow,
  moveEntry,
  changeSessionColor,
  changeBreakColor,
} from './util';

const entryTypeMapping = {
  Session: 'session',
  Break: 'break',
  Contribution: 'contribution',
};

const preprocessData = data => {
  // TODO remove this preprocessing once the backend returns the data in the correct format
  const blocks = Object.values(data)
    .map(e => Object.values(e))
    .flat();
  const childEntries = blocks
    .map(({id, entries}) =>
      entries ? Object.values(entries).map(v => ({...v, parentId: id})) : []
    )
    .flat();
  return [blocks, childEntries].map(en =>
    en.map(e => ({
      ..._.pick(e, [
        'id',
        'title',
        'slotTitle',
        'code',
        'sessionCode',
        'sessionId',
        'contributionId',
        'description',
        'parentId',
      ]),
      type: entryTypeMapping[e.entryType],
      start: new Date(Date.parse(`${e.startDate.date} ${e.startDate.time}`)),
      end: new Date(Date.parse(`${e.endDate.date} ${e.endDate.time}`)),
      attachmentCount: e.attachments?.files?.length + e.attachments?.folders.length, // TODO count files in folders
      color: e.entryType === 'Break' ? {text: e.textColor, background: e.color} : undefined,
      deleted: false,
    }))
  );
};

const preprocessSessionData = data => {
  return new Map(
    Object.entries(data).map(([, s]) => [
      s.id,
      {
        ..._.pick(s, ['title', 'isPoster']), // TODO get other attrs
        color: {text: s.textColor, background: s.color},
      },
    ])
  );
};

export default {
  entries: (
    state = {
      blocks: [],
      children: [],
      unscheduled: [],
      changes: [],
      currentChangeIdx: 0,
      selectedId: null,
      draggedIds: new Set(),
    },
    action
  ) => {
    switch (action.type) {
      case actions.SET_TIMETABLE_DATA:
        return {...state, ...preprocessEntries(...preprocessData(action.data))};
      case actions.MOVE_ENTRY:
        return {...state, ...moveEntry(state, action.args)};
      case actions.RESIZE_ENTRY:
        return {...state, ...resizeEntry(state, action.args)};
      case actions.SELECT_ENTRY:
        return {...state, selectedId: action.entry?.id};
      case actions.DELETE_ENTRY:
        return {...state, ...deleteEntry(state, action.entry), selectedId: null};
      case actions.DRAG_UNSCHEDULED_CONTRIBS:
        return {...state, draggedIds: action.contribIds};
      case actions.SCHEDULE_CONTRIBS:
        console.debug('SCHEDULE_CONTRIBS', action.contribs, action.args);
        return {
          ...state,
          ...scheduleContribs(state, action.contribs, action.args),
          draggedIds: new Set(),
        };
      case actions.CHANGE_COLOR:
        return action.sessionId ? state : {...state, ...changeBreakColor(state, action.color)};
      case actions.UNDO_CHANGE:
        return {
          ...state,
          currentChangeIdx: state.currentChangeIdx - 1,
        };
      case actions.REDO_CHANGE:
        return {
          ...state,
          currentChangeIdx: state.currentChangeIdx + 1,
        };
      default:
        return state;
    }
  },
  sessions: (state = [], action) => {
    switch (action.type) {
      case actions.SET_SESSION_DATA:
        return preprocessSessionData(action.data);
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
  display: (state = {mode: 'compact', showUnscheduled: false}, action) => {
    switch (action.type) {
      case actions.SET_DISPLAY_MODE:
        return {...state, mode: action.mode};
      case actions.TOGGLE_SHOW_UNSCHEDULED:
        return {...state, showUnscheduled: !state.showUnscheduled};
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
};
