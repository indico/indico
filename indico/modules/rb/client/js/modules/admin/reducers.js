// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {combineReducers} from 'redux';

import {camelizeKeys} from 'indico/utils/case';
import {requestReducer} from 'indico/utils/redux';

import {filterReducerFactory} from '../../common/filters';

import * as adminActions from './actions';

export const initialFilterStateFactory = () => ({
  text: null,
});

export default combineReducers({
  requests: combineReducers({
    settings: requestReducer(
      adminActions.FETCH_SETTINGS_REQUEST,
      adminActions.FETCH_SETTINGS_SUCCESS,
      adminActions.FETCH_SETTINGS_ERROR
    ),
    locations: requestReducer(
      adminActions.FETCH_LOCATIONS_REQUEST,
      adminActions.FETCH_LOCATIONS_SUCCESS,
      adminActions.FETCH_LOCATIONS_ERROR
    ),
    rooms: requestReducer(
      adminActions.FETCH_ROOMS_REQUEST,
      adminActions.FETCH_ROOMS_SUCCESS,
      adminActions.FETCH_ROOMS_ERROR
    ),
    equipmentTypes: requestReducer(
      adminActions.FETCH_EQUIPMENT_TYPES_REQUEST,
      adminActions.FETCH_EQUIPMENT_TYPES_SUCCESS,
      adminActions.FETCH_EQUIPMENT_TYPES_ERROR
    ),
    features: requestReducer(
      adminActions.FETCH_FEATURES_REQUEST,
      adminActions.FETCH_FEATURES_SUCCESS,
      adminActions.FETCH_FEATURES_ERROR
    ),
    attributes: requestReducer(
      adminActions.FETCH_ATTRIBUTES_REQUEST,
      adminActions.FETCH_ATTRIBUTES_SUCCESS,
      adminActions.FETCH_ATTRIBUTES_ERROR
    ),
  }),
  locations: (state = [], action) => {
    switch (action.type) {
      case adminActions.LOCATIONS_RECEIVED:
        return camelizeKeys(action.data);
      case adminActions.LOCATION_RECEIVED:
        return [...state.filter(loc => loc.id !== action.data.id), camelizeKeys(action.data)];
      case adminActions.LOCATION_DELETED:
        return state.filter(loc => loc.id !== action.id);
      default:
        return state;
    }
  },
  rooms: (state = [], action) => {
    switch (action.type) {
      case adminActions.ROOMS_RECEIVED:
        return camelizeKeys(action.data);
      case adminActions.ROOM_DELETED:
        return state.filter(room => room.id !== action.id);
      default:
        return state;
    }
  },
  settings: (state = {}, action) => {
    switch (action.type) {
      case adminActions.SETTINGS_RECEIVED:
        return action.data;
      default:
        return state;
    }
  },
  equipmentTypes: (state = [], action) => {
    switch (action.type) {
      case adminActions.EQUIPMENT_TYPES_RECEIVED:
        return camelizeKeys(action.data);
      case adminActions.EQUIPMENT_TYPE_RECEIVED:
        return [...state.filter(eq => eq.id !== action.data.id), camelizeKeys(action.data)];
      case adminActions.EQUIPMENT_TYPE_DELETED:
        return state.filter(eq => eq.id !== action.id);
      case adminActions.FEATURE_DELETED:
        return state.map(eq => ({
          ...eq,
          features: eq.features.filter(id => id !== action.id),
        }));
      default:
        return state;
    }
  },
  features: (state = [], action) => {
    switch (action.type) {
      case adminActions.FEATURES_RECEIVED:
        return action.data;
      case adminActions.FEATURE_RECEIVED:
        return [...state.filter(feat => feat.id !== action.data.id), action.data];
      case adminActions.FEATURE_DELETED:
        return state.filter(feat => feat.id !== action.id);
      default:
        return state;
    }
  },
  attributes: (state = [], action) => {
    switch (action.type) {
      case adminActions.ATTRIBUTES_RECEIVED:
        return camelizeKeys(action.data);
      case adminActions.ATTRIBUTE_RECEIVED:
        return [...state.filter(attr => attr.id !== action.data.id), camelizeKeys(action.data)];
      case adminActions.ATTRIBUTE_DELETED:
        return state.filter(attr => attr.id !== action.id);
      default:
        return state;
    }
  },
  filters: filterReducerFactory(adminActions.FILTER_NAMESPACE, initialFilterStateFactory),
});
