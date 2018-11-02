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
import camelizeKeys from 'indico/utils/camelize';
import {filterReducerFactory} from '../../common/filters';
import * as adminActions from './actions';


export const initialFilterStateFactory = () => ({
    showInactive: true,
    text: null,
});

export default combineReducers({
    requests: combineReducers({
        locations: requestReducer(
            adminActions.FETCH_LOCATIONS_REQUEST,
            adminActions.FETCH_LOCATIONS_SUCCESS,
            adminActions.FETCH_LOCATIONS_ERROR
        ),
    }),
    locations: (state = [], action) => {
        switch (action.type) {
            case adminActions.LOCATIONS_RECEIVED: {
                const data = camelizeKeys(action.data);
                return [...state, ...data.sort((a, b) => a.name.localeCompare(b.name))];
            }
            default:
                return state;
        }
    },
    filters: filterReducerFactory(adminActions.FILTER_NAMESPACE, initialFilterStateFactory),
});
