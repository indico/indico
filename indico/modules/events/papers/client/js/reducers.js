// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
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
    permissions: requestReducer(
      paperActions.FETCH_PAPER_PERMISSIONS_REQUEST,
      paperActions.FETCH_PAPER_PERMISSIONS_SUCCESS,
      paperActions.FETCH_PAPER_PERMISSIONS_ERROR
    ),
    judgment: requestReducer(
      paperActions.JUDGE_PAPER_REQUEST,
      paperActions.JUDGE_PAPER_SUCCESS,
      paperActions.JUDGE_PAPER_ERROR
    ),
  }),
  details: (state = null, action) => {
    switch (action.type) {
      case paperActions.FETCH_PAPER_DETAILS_SUCCESS:
      case paperActions.RESET_PAPER_JUDGMENT_SUCCESS:
      case paperActions.JUDGE_PAPER_SUCCESS:
        return camelizeKeys(action.data);
      case paperActions.DELETE_COMMENT_SUCCESS:
        return camelizeKeys(action.data.paper);
      default:
        return state;
    }
  },
  permissions: (state = null, action) => {
    switch (action.type) {
      case paperActions.FETCH_PAPER_PERMISSIONS_SUCCESS:
        return camelizeKeys(action.data);
      case paperActions.DELETE_COMMENT_SUCCESS: {
        const {commentId} = action.data;
        const {comments: oldComments} = state;
        const newComments = {
          view: oldComments.view.filter(id => id !== commentId),
          edit: oldComments.edit.filter(id => id !== commentId),
        };
        return {...state, comments: newComments};
      }
      default:
        return state;
    }
  },
});
