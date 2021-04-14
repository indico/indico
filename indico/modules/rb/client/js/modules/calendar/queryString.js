// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import {createQueryStringReducer, validator as v} from 'redux-router-querystring';

import * as actions from '../../actions';
import {actions as filtersActions} from '../../common/filters';
import {rules as roomSearchQueryStringRules} from '../../common/roomSearch/queryString';
import {history} from '../../history';
import {defaultStateField, boolStateField} from '../../util';

import * as calendarActions from './actions';
import {initialState} from './reducers';

const rules = {
  ...roomSearchQueryStringRules,
  date: {
    validator: date => v.isDate(date) && moment(date).isBetween('1970-01-01', '2999-12-31'),
    stateField: 'datePicker.selectedDate',
  },
  mode: {
    validator: v.isIn(['days', 'weeks', 'months']),
    stateField: defaultStateField('datePicker.mode', 'days'),
  },
  my_bookings: {
    validator: v.isBoolean(),
    sanitizer: v.toBoolean(),
    stateField: boolStateField('filters.myBookings'),
  },
  hide_unused: {
    validator: v.isBoolean(),
    sanitizer: v.toBoolean(),
    stateField: boolStateField('filters.hideUnused'),
  },
  show_inactive: {
    validator: v.isBoolean(),
    sanitizer: v.toBoolean(),
    stateField: boolStateField('filters.showInactive'),
  },
  view: {
    validator: v.isIn(['timeline', 'list']),
    stateField: defaultStateField('view', 'calendar'),
  },
};

export const routeConfig = {
  '/calendar': {
    listen: [
      filtersActions.SET_FILTER_PARAMETER,
      filtersActions.SET_FILTERS,
      calendarActions.SET_DATE,
      calendarActions.SET_MODE,
      calendarActions.CHANGE_VIEW,
    ],
    select: ({calendar}) => calendar,
    serialize: rules,
  },
};

export const queryStringReducer = createQueryStringReducer(
  rules,
  (state, action) => {
    if (action.type === actions.INIT) {
      return {
        namespace: 'calendar',
        queryString: history.location.search.slice(1),
      };
    }
    return null;
  },
  (state, namespace) =>
    namespace ? _.merge({}, state, _.set({}, namespace, initialState())) : state
);
