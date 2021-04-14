// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {combineReducers} from 'redux';

import {camelizeKeys} from 'indico/utils/case';
import {requestReducer} from 'indico/utils/redux';

import * as paperActions from './actions';

export default combineReducers({
  requests: combineReducers({
    details: requestReducer(
      paperActions.FETCH_PAPER_DETAILS_REQUEST,
      paperActions.FETCH_PAPER_DETAILS_SUCCESS,
      paperActions.FETCH_PAPER_DETAILS_ERROR
    ),
    resetState: requestReducer(
      paperActions.RESET_PAPER_JUDGMENT_REQUEST,
      paperActions.RESET_PAPER_JUDGMENT_SUCCESS,
      paperActions.RESET_PAPER_JUDGMENT_ERROR
    ),
    deleteComment: requestReducer(
      paperActions.DELETE_COMMENT_REQUEST,
      paperActions.DELETE_COMMENT_SUCCESS,
      paperActions.DELETE_COMMENT_ERROR
    ),
  }),
  details: (state = null, action) => {
    switch (action.type) {
      case paperActions.FETCH_PAPER_DETAILS_SUCCESS:
        return camelizeKeys(action.data);
      default:
        return state;
    }
  },
});
