// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

import {
  CREATE_ITEM,
  CREATE_SECTION,
  LOCK_UI,
  MOVE_ITEM,
  MOVE_SECTION,
  REMOVE_ITEM,
  REMOVE_SECTION,
  SET_FORM_DATA,
  TOGGLE_SECTION,
  UNLOCK_UI,
  UPDATE_ITEM,
  UPDATE_POSITIONS,
  UPDATE_SECTION,
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
      case CREATE_ITEM:
        return {
          ...state,
          [action.data.id]: action.data,
        };
      case UPDATE_ITEM:
        return {...state, [action.itemId]: action.data};
      case UPDATE_POSITIONS: {
        const newState = {...state};
        Object.entries(action.items)
          .filter(([id]) => id in newState)
          .forEach(([id, position]) => {
            newState[id] = {...newState[id], position};
          });
        return newState;
      }
      case REMOVE_ITEM:
        return _.omit(state, action.itemId);
      case REMOVE_SECTION:
        return _.omitBy(state, item => item.sectionId === action.sectionId);
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
      case TOGGLE_SECTION:
        return {
          ...state,
          [action.sectionId]: {...state[action.sectionId], enabled: action.enabled},
        };
      case CREATE_SECTION:
        return {
          ...state,
          [action.data.id]: action.data,
        };
      case UPDATE_SECTION:
        return {
          ...state,
          [action.sectionId]: action.patch
            ? {...state[action.sectionId], ...action.data}
            : action.data,
        };
      case UPDATE_POSITIONS: {
        const newState = {...state};
        Object.entries(action.sections)
          .filter(([id]) => id in newState)
          .forEach(([id, position]) => {
            newState[id] = {...newState[id], position};
          });
        return newState;
      }
      case REMOVE_SECTION:
        return _.omit(state, action.sectionId);
      case MOVE_SECTION: {
        const sorted = _.sortBy(Object.values(state), ['position', 'id']);
        const sourceSection = sorted[action.sourceIndex];
        sorted.splice(action.sourceIndex, 1);
        sorted.splice(action.targetIndex, 0, sourceSection);
        // use same positioning logic as on the server side. not sure if it's needed, we
        // could probably stick with just incrementing, but it might avoid some re-renders..
        let enabledPos = 1;
        let disabledPos = 1000;
        const newState = {...state};
        sorted.forEach(section => {
          newState[section.id] = {
            ...section,
            position: section.enabled ? enabledPos++ : disabledPos++,
          };
        });
        return newState;
      }
      default:
        return state;
    }
  },
};
