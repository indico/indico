// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {SET_FORM_DATA, SET_HIDDEN_ITEM_IDS} from './actions';

export default {
  items: (state = {}, action) => {
    switch (action.type) {
      case SET_FORM_DATA:
        return action.items;
      default:
        return state;
    }
  },
  sections: (state = {}, action) => {
    switch (action.type) {
      case SET_FORM_DATA:
        return action.sections;
      default:
        return state;
    }
  },
  hiddenItemIds: (state = [], action) => {
    switch (action.type) {
      case SET_HIDDEN_ITEM_IDS:
        return action.hiddenItemIds;
      default:
        return state;
    }
  },
};
