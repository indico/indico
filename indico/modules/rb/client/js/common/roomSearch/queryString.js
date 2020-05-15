// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createQueryStringReducer, validator as v} from 'redux-router-querystring';
import {LOCATION_CHANGE} from 'connected-react-router';

import {history} from '../../history';
import * as actions from '../../actions';
import {initialRoomFilterStateFactory} from './reducers';
import {boolStateField} from '../../util';

export const rules = {
  recurrence: {
    validator: v.isIn(['single', 'daily', 'every']),
    stateField: 'filters.recurrence.type',
  },
  number: {
    validator: v.isInt({min: 1, max: 99}),
    sanitizer: v.toInt(),
    stateField: 'filters.recurrence.number',
  },
  interval: {
    validator: v.isIn(['week', 'month']),
    stateField: 'filters.recurrence.interval',
  },
  sd: {
    validator: v.isDate(),
    stateField: 'filters.dates.startDate',
  },
  ed: {
    validator: v.isDate(),
    stateField: 'filters.dates.endDate',
  },
  st: {
    validator: v.isTime(),
    stateField: 'filters.timeSlot.startTime',
  },
  et: {
    validator: v.isTime(),
    stateField: 'filters.timeSlot.endTime',
  },
  favorite: {
    validator: v.isBoolean(),
    sanitizer: v.toBoolean(),
    stateField: boolStateField('filters.onlyFavorites'),
  },
  mine: {
    validator: v.isBoolean(),
    sanitizer: v.toBoolean(),
    stateField: boolStateField('filters.onlyMine'),
  },
  authorized: {
    validator: v.isBoolean(),
    sanitizer: v.toBoolean(),
    stateField: boolStateField('filters.onlyAuthorized'),
  },
  capacity: {
    validator: v.isInt({min: 1}),
    sanitizer: v.toInt(),
    stateField: 'filters.capacity',
  },
  eq: {
    validator: () => true,
    stateField: {
      serialize: ({filters: {equipment}}) => equipment,
      parse: (value, state) => {
        if (!Array.isArray(value)) {
          value = [value];
        }
        if (!state.filters) {
          state.filters = {};
        }
        state.filters.equipment = value;
      },
    },
  },
  feat: {
    validator: () => true,
    stateField: {
      serialize: ({filters: {features}}) => features,
      parse: (value, state) => {
        if (!Array.isArray(value)) {
          value = [value];
        }
        if (!state.filters) {
          state.filters = {};
        }
        state.filters.features = value;
      },
    },
  },
  building: {
    stateField: 'filters.building',
  },
  text: {
    stateField: 'filters.text',
  },
  division: {
    stateField: 'filters.division',
  },
  sw_lat: {
    validator: v.isFloat({min: -90, max: 90}),
    sanitizer: v.toFloat(),
    stateField: 'filters.bounds.SW[0]',
  },
  sw_lng: {
    validator: v.isFloat({min: -180, max: 180}),
    sanitizer: v.toFloat(),
    stateField: 'filters.bounds.SW[1]',
  },
  ne_lat: {
    validator: v.isFloat({min: -90, max: 90}),
    sanitizer: v.toFloat(),
    stateField: 'filters.bounds.NE[0]',
  },
  ne_lng: {
    validator: v.isFloat({min: -180, max: 180}),
    sanitizer: v.toFloat(),
    stateField: 'filters.bounds.NE[1]',
  },
};

function pathMatch(map, path) {
  for (const pth in map) {
    if (new RegExp(pth).test(path)) {
      return map[pth];
    }
  }
}

export const queryStringReducer = createQueryStringReducer(
  rules,
  (state, action) => {
    if (action.type === actions.INIT || action.type === LOCATION_CHANGE) {
      let pathname, queryString;
      if (action.type === actions.INIT) {
        pathname = history.location.pathname;
        queryString = history.location.search;
      } else {
        pathname = action.payload.location.pathname;
        queryString = action.payload.location.search;
      }

      const namespace = pathMatch(
        {
          '^/book': 'bookRoom',
          '^/rooms': 'roomList',
        },
        pathname
      );
      if (!namespace) {
        return null;
      }
      return {
        namespace,
        queryString: queryString.slice(1),
      };
    }
    return null;
  },
  (state, namespace, error_ = false) =>
    namespace
      ? _.merge({}, state, {
          [namespace]: {
            filters: {
              ...initialRoomFilterStateFactory(namespace),
              error: error_ ? error_ : state[namespace].filters.error,
            },
          },
        })
      : state
);
