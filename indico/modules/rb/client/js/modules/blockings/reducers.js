// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {combineReducers} from 'redux';

import {camelizeKeys} from 'indico/utils/case';
import {requestReducer} from 'indico/utils/redux';

import {filterReducerFactory} from '../../common/filters';

import * as blockingsActions from './actions';

export const initialFilterStateFactory = () => ({
  myBlockings: false,
  myRooms: false,
  timeframe: 'recent',
});

export default combineReducers({
  requests: combineReducers({
    blockings: requestReducer(
      blockingsActions.FETCH_BLOCKINGS_REQUEST,
      blockingsActions.FETCH_BLOCKINGS_SUCCESS,
      blockingsActions.FETCH_BLOCKINGS_ERROR
    ),
    blocking: requestReducer(
      blockingsActions.FETCH_BLOCKING_REQUEST,
      blockingsActions.FETCH_BLOCKING_SUCCESS,
      blockingsActions.FETCH_BLOCKING_ERROR
    ),
    create: requestReducer(
      blockingsActions.CREATE_BLOCKING_REQUEST,
      blockingsActions.CREATE_BLOCKING_SUCCESS,
      blockingsActions.CREATE_BLOCKING_ERROR
    ),
    blockingState: requestReducer(
      blockingsActions.CHANGE_BLOCKING_STATE_REQUEST,
      blockingsActions.CHANGE_BLOCKING_STATE_SUCCESS,
      blockingsActions.CHANGE_BLOCKING_STATE_ERROR
    ),
    delete: requestReducer(
      blockingsActions.DELETE_BLOCKING_REQUEST,
      blockingsActions.DELETE_BLOCKING_SUCCESS,
      blockingsActions.DELETE_BLOCKING_ERROR
    ),
  }),
  blockings: (state = {}, action) => {
    switch (action.type) {
      case blockingsActions.BLOCKINGS_RECEIVED:
        return action.data.reduce((obj, b) => ({...obj, [b.id]: camelizeKeys(b)}), {});
      case blockingsActions.BLOCKING_RECEIVED:
        return {...state, [action.data.id]: camelizeKeys(action.data)};
      case blockingsActions.CHANGE_BLOCKING_STATE_SUCCESS: {
        const {blocking} = camelizeKeys(action.data);
        return {...state, [blocking.id]: blocking};
      }
      case blockingsActions.DELETE_BLOCKING_SUCCESS: {
        const {blockingId} = camelizeKeys(action.data);
        return _.omit(state, blockingId);
      }
      default:
        return state;
    }
  },
  filters: filterReducerFactory(blockingsActions.FILTER_NAMESPACE, initialFilterStateFactory),
});
