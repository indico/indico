// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {SET_LOADING, SET_DETAILS} from './actions';
import {processRevisions} from './selectors';

export const initialState = {
  details: null,
  timelineBlocks: null,
  isLoading: false,
};

export default function reducer(state = initialState, action) {
  switch (action.type) {
    case SET_LOADING:
      return {...state, isLoading: true};
    case SET_DETAILS:
      return {
        ...state,
        details: action.data,
        isLoading: false,
        timelineBlocks: processRevisions(action.data.revisions),
      };
    default:
      return state;
  }
}
