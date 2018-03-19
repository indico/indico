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

/* global process:false */

import React from 'react';
import ReactDOM from 'react-dom';
import EventLog from './components/EventLog';
import {createStore, applyMiddleware, compose} from 'redux';
import {Provider} from 'react-redux';
import thunkMiddleware from 'redux-thunk';
import logger from 'redux-logger';
import globalReducer from './reducers';
import {fetchPosts} from './actions';

import '../style/logs.scss';

window.addEventListener('load', () => {
    const rootElement = document.getElementById('event-log');
    const fetchLogsUrl = rootElement.dataset.fetchLogsUrl;
    const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;
    const store = createStore(globalReducer, composeEnhancers(
        applyMiddleware(
            thunkMiddleware.withExtraArgument(fetchLogsUrl),
            process.env.NODE_ENV === 'development' ? logger : null
        )
    ));

    ReactDOM.render(
        <Provider store={store}>
            <EventLog />
        </Provider>,
        rootElement
    );

    store.dispatch(fetchPosts());
});
