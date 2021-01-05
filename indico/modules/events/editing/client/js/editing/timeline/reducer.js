// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {camelizeKeys} from 'indico/utils/case';

import {SET_LOADING, SET_DETAILS, SET_NEW_DETAILS} from './actions';
import {processRevisions} from './util';

export const initialState = {
  details: null,
  newDetails: null,
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
        newDetails: details,
        loading: false,
        timelineBlocks: processRevisions(details.revisions),
      };
    }
    case SET_NEW_DETAILS: {
      const newDetails = camelizeKeys(action.data);
      return {...state, newDetails};
    }
    default:
      return state;
  }
}
