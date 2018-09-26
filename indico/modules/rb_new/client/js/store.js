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
import createHistory from 'history/createBrowserHistory';
import {queryStringMiddleware, createQueryStringReducer} from 'redux-router-querystring';
import {connectRouter, routerMiddleware, LOCATION_CHANGE} from 'connected-react-router';
import createReduxStore from 'indico/utils/redux';

import reducers from './reducers';
import {initialRoomFilterStateFactory} from './reducers/roomBooking/filters';
import {routeConfig as bookRoomRouteConfig, queryStringReducer as qsBookRoomReducer} from './modules/bookRoom';
import {routeConfig as calendarRouteConfig, queryStringReducer as qsCalendarReducer} from './modules/calendar';
import {routeConfig as blockingsRouteConfig, queryStringReducer as qsBlockingsReducer} from './modules/blockings';
import * as actions from './actions';
import {queryString as queryFilterRules} from './serializers/filters';


function getRouteConfig() {
    return {
        reduxPathname: ({router: {location: {pathname}}}) => pathname,
        routes: {
            '/rooms': {
                listen: actions.SET_FILTER_PARAMETER,
                select: ({roomList: {filters}}) => ({filters}),
                serialize: queryFilterRules
            },
            ...bookRoomRouteConfig,
            ...calendarRouteConfig,
            ...blockingsRouteConfig,
        }
    };
}

function pathMatch(map, path) {
    for (const pth in map) {
        if (new RegExp(pth).test(path)) {
            return map[pth];
        }
    }
}

export const history = createHistory({
    basename: '/rooms-new'
});

const qsFilterReducer = createQueryStringReducer(
    queryFilterRules,
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

            const namespace = pathMatch({
                '^/book': 'bookRoom',
                '^/rooms': 'roomList'
            }, pathname);
            if (!namespace) {
                return null;
            }
            return {
                namespace,
                queryString: queryString.slice(1)
            };
        }
        return null;
    },
    (state, namespace) => (namespace
        ? _.merge({}, state, {[namespace]: {filters: initialRoomFilterStateFactory(namespace)}})
        : state)
);

export default function createRBStore(overrides = {}) {
    return createReduxStore(
        'rb-new',
        reducers,
        {_overrides: overrides},
        [
            routerMiddleware(history),
            queryStringMiddleware(history, getRouteConfig(), {usePush: false})
        ],
        [
            qsFilterReducer,
            qsBookRoomReducer,
            qsCalendarReducer,
            qsBlockingsReducer,
        ],
        rootReducer => connectRouter(history)(rootReducer));
}
