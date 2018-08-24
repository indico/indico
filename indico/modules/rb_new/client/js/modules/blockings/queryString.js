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

import _ from 'lodash';
import {createQueryStringReducer, validator as v} from 'redux-router-querystring';

import {history} from '../../store';
import {initialFilterStateFactory} from './reducers';
import * as actions from '../../actions';
import {boolStateField} from '../../util';


const rules = {
    sd: {
        validator: v.isDate(),
        stateField: 'dates.startDate'
    },
    ed: {
        validator: v.isDate(),
        stateField: 'dates.endDate'
    },
    myRooms: {
        stateField: boolStateField('myRooms'),
        validator: v.isBoolean(),
        sanitizer: v.toBoolean()
    },
    myBlockings: {
        stateField: boolStateField('myBlockings'),
        validator: v.isBoolean(),
        sanitizer: v.toBoolean()
    },
};


export const routeConfig = {
    '/blockings': {
        listen: actions.SET_FILTER_PARAMETER,
        select: ({blockings: {filters}}) => filters,
        serialize: rules,
    }
};


export const queryStringReducer = createQueryStringReducer(
    rules,
    (state, action) => {
        if (action.type === actions.INIT) {
            return {
                namespace: 'blockings.filters',
                queryString: history.location.search.slice(1)
            };
        }
        return null;
    },
    (state, namespace) => (namespace
        ? _.merge({}, state, _.set({}, namespace, initialFilterStateFactory()))
        : state)
);
