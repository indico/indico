// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {routerMiddleware} from 'connected-react-router';
import {queryStringMiddleware} from 'redux-router-querystring';

import createReduxStore from 'indico/utils/redux';

import {queryStringReducer as qsRoomSearchReducer} from './common/roomSearch/queryString';
import {history} from './history';
import {
  routeConfig as blockingsRouteConfig,
  queryStringReducer as qsBlockingsReducer,
} from './modules/blockings/queryString';
import {
  routeConfig as bookRoomRouteConfig,
  queryStringReducer as qsBookRoomReducer,
} from './modules/bookRoom/queryString';
import {
  routeConfig as calendarRouteConfig,
  queryStringReducer as qsCalendarReducer,
} from './modules/calendar/queryString';
import {routeConfig as roomListRouteConfig} from './modules/roomList/queryString';
import getReducers from './reducers';

function getRouteConfig() {
  return {
    reduxPathname: ({
      router: {
        location: {pathname},
      },
    }) => pathname,
    routes: {
      ...roomListRouteConfig,
      ...bookRoomRouteConfig,
      ...calendarRouteConfig,
      ...blockingsRouteConfig,
    },
  };
}

/**
 * Create the redux store of the RB module.
 *
 * @param {Object} overrides - overrides provided by e.g. a plugin
 * @param {Array} additionalReducers - additional reducers provided by
 * e.g. a plugin
 */
export default function createRBStore(additionalReducers = []) {
  return createReduxStore(
    'rb-new',
    getReducers(history),
    {},
    [routerMiddleware(history), queryStringMiddleware(history, getRouteConfig(), {usePush: false})],
    [
      qsRoomSearchReducer,
      qsBookRoomReducer,
      qsCalendarReducer,
      qsBlockingsReducer,
      ...additionalReducers,
    ]
  );
}
