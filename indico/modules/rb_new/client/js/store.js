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

import {createBrowserHistory} from 'history';
import {queryStringMiddleware} from 'redux-router-querystring';
import {routerMiddleware} from 'connected-react-router';
import createReduxStore from 'indico/utils/redux';

import getReducers from './reducers';
import {queryStringReducer as qsRoomSearchReducer} from './common/roomSearch';
import {routeConfig as roomListRouteConfig} from './modules/roomList';
import {routeConfig as bookRoomRouteConfig, queryStringReducer as qsBookRoomReducer} from './modules/bookRoom';
import {routeConfig as calendarRouteConfig, queryStringReducer as qsCalendarReducer} from './modules/calendar';
import {routeConfig as blockingsRouteConfig, queryStringReducer as qsBlockingsReducer} from './modules/blockings';


function getRouteConfig() {
    return {
        reduxPathname: ({router: {location: {pathname}}}) => pathname,
        routes: {
            ...roomListRouteConfig,
            ...bookRoomRouteConfig,
            ...calendarRouteConfig,
            ...blockingsRouteConfig,
        }
    };
}

export const history = createBrowserHistory({
    basename: `${Indico.Urls.BasePath}/rooms-new`
});

/**
 * Create the redux store of the RB module.
 *
 * @param {Object} overrides - overrides provided by e.g. a plugin
 * @param {Array} additionalReducers - additional reducers provided by
 * e.g. a plugin
 */
export default function createRBStore(overrides = {}, additionalReducers = []) {
    return createReduxStore(
        'rb-new',
        getReducers(history),
        {_overrides: overrides},
        [
            routerMiddleware(history),
            queryStringMiddleware(history, getRouteConfig(), {usePush: false})
        ],
        [
            qsRoomSearchReducer,
            qsBookRoomReducer,
            qsCalendarReducer,
            qsBlockingsReducer,
            ...additionalReducers
        ]);
}
