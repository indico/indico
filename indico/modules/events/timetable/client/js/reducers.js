// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import * as actions from './actions';
import {moveEntry, processEntries, resizeWindow} from './util';

const preprocessData = data => {
  // TODO remove this preprocessing once the backend returns the data in the correct format
  const sessionBlocks = Object.values(data)
    .map(e => Object.values(e))
    .flat();
  const contribs = sessionBlocks
    .map(e => (e.entries ? Object.values(e.entries).map(v => ({...v, parent: e.id})) : []))
    .flat();
  return [sessionBlocks, contribs].map(en =>
    en.map(e => ({
      id: e.id,
      title: e.title,
      start: new Date(Date.parse(`${e.startDate.date} ${e.startDate.time}`)),
      end: new Date(Date.parse(`${e.endDate.date} ${e.endDate.time}`)),
      desc: e.description,
      color: {text: e.textColor, background: e.color},
      parent: e.parent,
    }))
  );
};

export default {
  entries: (state = {sessionBlocks: [], contributions: []}, action) => {
    switch (action.type) {
      case actions.SET_TIMETABLE_DATA:
        return processEntries(...preprocessData(action.data));
      case actions.MOVE_ENTRY:
        return moveEntry(state, action);
      case actions.RESIZE_ENTRY:
        return moveEntry(state, action);
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
  compactMode: (state = true, action) => {
    switch (action.type) {
      case actions.TOGGLE_COMPACT_MODE:
        return !state;
      default:
        return state;
    }
  },
};
