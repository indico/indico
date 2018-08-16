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

import * as actions from '../../actions';
import {history} from '../../store';
import {initialState} from './reducers';
import {SET_DATE} from './actions';


const rules = {
    date: {
        validator: (date) => v.isDate(date) && moment(date).isBetween('1970-01-01', '2999-12-31'),
        stateField: 'date'
    }
};


export const routeConfig = {
    '/calendar': {
        listen: SET_DATE,
        select: ({calendar: {data}}) => data,
        serialize: rules,
    }
};


export const queryStringReducer = createQueryStringReducer(
    rules,
    (state, action) => {
        if (action.type === actions.INIT) {
            return {
                namespace: 'calendar.data',
                queryString: history.location.search.slice(1)
            };
        }
        return null;
    },
    (state, namespace) => (namespace
        ? _.merge({}, state, _.set({}, namespace, initialState))
        : state)
);
