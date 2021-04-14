// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createQueryStringReducer, validator as v} from 'redux-router-querystring';

import * as actions from '../../actions';
import {actions as filtersActions} from '../../common/filters';
import {history} from '../../history';
import {boolStateField} from '../../util';

import {initialFilterStateFactory} from './reducers';

const rules = {
  my_rooms: {
    stateField: boolStateField('myRooms'),
    validator: v.isBoolean(),
    sanitizer: v.toBoolean(),
  },
  my_blockings: {
    stateField: boolStateField('myBlockings'),
    validator: v.isBoolean(),
    sanitizer: v.toBoolean(),
  },
  timeframe: {
    stateField: 'timeframe',
    validator: v.isIn(['recent', 'year', 'all']),
  },
};

export const routeConfig = {
  '/blockings': {
    listen: [filtersActions.SET_FILTER_PARAMETER, filtersActions.SET_FILTERS],
    select: ({blockings: {filters}}) => filters,
    serialize: rules,
  },
};

export const queryStringReducer = createQueryStringReducer(
  rules,
  (state, action) => {
    if (action.type === actions.INIT) {
      return {
        namespace: 'blockings.filters',
        queryString: history.location.search.slice(1),
      };
    }
    return null;
  },
  (state, namespace) =>
    namespace ? _.merge({}, state, _.set({}, namespace, initialFilterStateFactory())) : state
);
