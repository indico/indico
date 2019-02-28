/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import {combineReducers} from 'redux';
import {requestReducer} from 'indico/utils/redux';
import {camelizeKeys} from 'indico/utils/case';
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
                return [
                    ...state.filter(eq => eq.id !== action.data.id),
                    camelizeKeys(action.data),
                ];
            case adminActions.EQUIPMENT_TYPE_DELETED:
                return state.filter(eq => eq.id !== action.id);
            case adminActions.FEATURE_DELETED:
                return state.map(eq => ({
                    ...eq,
                    features: eq.features.filter(id => id !== action.id)
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
                return [
                    ...state.filter(feat => feat.id !== action.data.id),
                    action.data,
                ];
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
                return [
                    ...state.filter(attr => attr.id !== action.data.id),
                    camelizeKeys(action.data),
                ];
            case adminActions.ATTRIBUTE_DELETED:
                return state.filter(attr => attr.id !== action.id);
            default:
                return state;
        }
    },
    filters: filterReducerFactory(adminActions.FILTER_NAMESPACE, initialFilterStateFactory),
});
