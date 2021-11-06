// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

import {
  LOCK_UI,
  MOVE_ITEM,
  MOVE_SECTION,
  REMOVE_ITEM,
  SET_FORM_DATA,
  UNLOCK_UI,
  UPDATE_ITEM,
} from './actions';

export default {
  uiLocked: (state = false, action) => {
    switch (action.type) {
      case LOCK_UI:
        return true;
      case UNLOCK_UI:
        return false;
      default:
        return state;
    }
  },
  items: (state = {}, action) => {
    switch (action.type) {
      case SET_FORM_DATA:
        return action.items;
      case UPDATE_ITEM:
        return {...state, [action.itemId]: action.data};
      case REMOVE_ITEM:
        return _.omit(state, action.itemId);
      case MOVE_ITEM: {
        const sorted = _.sortBy(
          Object.values(state).filter(f => f.sectionId === action.sectionId),
          ['position', 'id']
        );
        const sourceItem = sorted[action.sourceIndex];
        sorted.splice(action.sourceIndex, 1);
        sorted.splice(action.targetIndex, 0, sourceItem);
        // use same positioning logic as on the server side. not sure if it's needed, we
        // could probably stick with just incrementing, but it might avoid some re-renders..
        let enabledPos = 1;
        let disabledPos = 1000;
        const newState = {...state};
        sorted.forEach(item => {
          newState[item.id] = {...item, position: item.isEnabled ? enabledPos++ : disabledPos++};
        });
        return newState;
      }
      default:
        return state;
    }
  },
  sections: (state = {}, action) => {
    switch (action.type) {
      case SET_FORM_DATA:
        return action.sections;
      case MOVE_SECTION: {
        const sorted = _.sortBy(Object.values(state), ['position', 'id']);
        const sourceSection = sorted[action.sourceIndex];
        sorted.splice(action.sourceIndex, 1);
        sorted.splice(action.targetIndex, 0, sourceSection);
        const newState = {...state};
        sorted.forEach((section, index) => {
          newState[section.id] = {...section, position: index + 1};
        });
        return newState;
      }
      default:
        return state;
    }
  },
};
