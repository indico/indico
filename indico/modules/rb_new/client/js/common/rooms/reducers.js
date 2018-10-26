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

import camelizeKeys from 'indico/utils/camelize';
import {requestReducer} from 'indico/utils/redux';
import * as roomsActions from './actions';


export default combineReducers({
    requests: combineReducers({
        // global data
        equipmentTypes: requestReducer(
            roomsActions.FETCH_EQUIPMENT_TYPES_REQUEST,
            roomsActions.FETCH_EQUIPMENT_TYPES_SUCCESS,
            roomsActions.FETCH_EQUIPMENT_TYPES_ERROR
        ),
        // room-specific data
        rooms: requestReducer(
            roomsActions.FETCH_ROOMS_REQUEST,
            roomsActions.FETCH_ROOMS_SUCCESS,
            roomsActions.FETCH_ROOMS_ERROR
        ),
        availability: requestReducer(
            roomsActions.FETCH_AVAILABILITY_REQUEST,
            roomsActions.FETCH_AVAILABILITY_SUCCESS,
            roomsActions.FETCH_AVAILABILITY_ERROR
        ),
        attributes: requestReducer(
            roomsActions.FETCH_ATTRIBUTES_REQUEST,
            roomsActions.FETCH_ATTRIBUTES_SUCCESS,
            roomsActions.FETCH_ATTRIBUTES_ERROR
        ),
    }),
    equipmentTypes: (state = [], action) => {
        switch (action.type) {
            case roomsActions.EQUIPMENT_TYPES_RECEIVED:
                return action.data.map(x => camelizeKeys(x)).reduce((obj, r) => ({...obj, [r.id]: r}), {});
            default:
                return state;
        }
    },
    rooms: (state = {}, action) => {
        switch (action.type) {
            case roomsActions.ROOMS_RECEIVED:
                return action.data;
            default:
                return state;
        }
    },
    availability: (state = {}, action) => {
        switch (action.type) {
            case roomsActions.AVAILABILITY_RECEIVED: {
                const {id, availability} = action.data;
                return {...state, [id]: availability};
            }
            default:
                return state;
        }
    },
    attributes: (state = {}, action) => {
        switch (action.type) {
            case roomsActions.ATTRIBUTES_RECEIVED: {
                const {id, attributes} = action.data;
                return {...state, [id]: attributes};
            }
            default:
                return state;
        }
    },
});
