// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import * as globalActions from '../../actions';

import * as filtersActions from './actions';

export function filterReducerFactory(namespace, initialState, postprocess = x => x) {
  let factory;
  if (typeof initialState === 'function') {
    factory = initialState;
  } else {
    factory = () => initialState;
  }
  return (state = factory(namespace), action) => {
    switch (action.type) {
      case filtersActions.SET_FILTER_PARAMETER:
        return action.namespace === namespace
          ? postprocess({...state, [action.param]: action.data}, action.param)
          : state;
      case filtersActions.SET_FILTERS:
        if (action.namespace !== namespace) {
          return state;
        } else if (action.merge) {
          return {...state, ...action.params};
        } else {
          return {...factory(namespace), ...action.params};
        }
      case globalActions.RESET_PAGE_STATE:
        return !action.namespace || action.namespace === namespace ? factory(namespace) : state;
      default:
        return state;
    }
  };
}
