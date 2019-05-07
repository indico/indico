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
import {boolStateField, defaultStateField} from '../../util';

import * as globalActions from '../../actions';
import * as actions from './actions';
import {history} from '../../store';
import {initialTimelineState} from './reducers';
import {actions as filtersActions} from '../../common/filters';
import {queryStringRules as queryFilterRules} from '../../common/roomSearch';


export const rules = {
    timeline: {
        validator: v.isBoolean(),
        sanitizer: v.toBoolean(),
        stateField: boolStateField('timeline.data.isVisible')
    },
    mode: {
        validator: v.isIn(['days', 'weeks', 'months']),
        stateField: defaultStateField('timeline.datePicker.mode', 'days'),
    },
};

export const routeConfig = {
    '/book': [
        {
            listen: [filtersActions.SET_FILTER_PARAMETER, filtersActions.SET_FILTERS],
            select: ({bookRoom: {filters}}) => ({filters}),
            serialize: queryFilterRules
        },
        {
            listen: [
                actions.TOGGLE_TIMELINE_VIEW,
                actions.SET_TIMELINE_MODE
            ],
            select: ({bookRoom: {timeline}}) => ({timeline}),
            serialize: rules
        },
    ]
};

export const queryStringReducer = createQueryStringReducer(
    rules,
    (state, action) => {
        if (action.type === globalActions.INIT) {
            return {
                namespace: 'bookRoom',
                queryString: history.location.search.slice(1)
            };
        }
        return null;
    },
    (state, namespace) => (namespace
        ? _.merge({}, state, {[namespace]: {timeline: {data: initialTimelineState}}})
        : state)
);
