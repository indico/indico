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
import {routerReducer, routerMiddleware} from 'react-router-redux';
import createReduxStore from 'indico/utils/redux';

import {userReducer, bookRoomReducer, roomListReducer} from './reducers';
import {initialStateFactory} from './reducers/roomBooking/filters';
import {SET_FILTER_PARAMETER} from './actions';
import {queryString as queryFilterRules} from './serializers/filters';


const initialData = {
    staticData: {}
};

const routeConfig = {
    reduxPathname: ({router: {location: {pathname}}}) => pathname,
    routes: {
        '/book': {
            listen: SET_FILTER_PARAMETER,
            select: ({bookRoom: {filters}}) => ({filters}),
            serialize: queryFilterRules
        },
        '/rooms': {
            listen: SET_FILTER_PARAMETER,
            select: ({roomList: {filters}}) => ({filters}),
            serialize: queryFilterRules
        }
    }
};

const qsReducer = createQueryStringReducer(
    queryFilterRules,
    (state, action) => {
        if (action.type === '@@router/LOCATION_CHANGE') {
            const {payload: {search, pathname}} = action;
            return {
                namespace: {
                    '/book': 'bookRoom',
                    '/rooms': 'roomList'
                }[pathname],
                queryString: search.slice(1)
            };
        }
        return null;
    },
    (state, namespace) => (namespace
        ? _.merge({}, state, {[namespace]: {filters: initialStateFactory(namespace)}})
        : state)
);

export const history = createHistory({
    basename: '/rooms-new'
});

export default function createRBStore(data) {
    return createReduxStore({
        user: userReducer,
        bookRoom: bookRoomReducer,
        roomList: roomListReducer,
        router: routerReducer
    }, Object.assign(initialData, data), [
        routerMiddleware(history),
        queryStringMiddleware(history, routeConfig)
    ], [
        qsReducer
    ]);
}
