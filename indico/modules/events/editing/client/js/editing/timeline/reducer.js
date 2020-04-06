// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {camelizeKeys} from 'indico/utils/case';

import {SET_LOADING, SET_DETAILS} from './actions';
import {processRevisions} from './selectors';

export const initialState = {
  details: null,
  timelineBlocks: null,
  loading: false,
};

export default function reducer(state = initialState, action) {
  switch (action.type) {
    case SET_LOADING:
      return {...state, loading: true};
    case SET_DETAILS: {
      const details = camelizeKeys(action.data);
      return {
        ...state,
        details,
        loading: false,
        timelineBlocks: processRevisions(details.revisions),
      };
    }
    default:
      return state;
  }
}
