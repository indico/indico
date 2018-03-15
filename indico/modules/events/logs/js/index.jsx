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

import React from 'react';
import ReactDOM from 'react-dom';
import EventLog from './components/EventLog';
import { createStore } from 'redux';
import { Provider } from 'react-redux';
import globalReducer from './reducers';

import '../style/logs.scss';

const store = createStore(globalReducer);

window.addEventListener('load', () => {
    ReactDOM.render(
        <Provider store={store}>
            <EventLog />
        </Provider>,
        document.getElementById('event-log')
    );
});

// XXX: delete this whenever we have real data
store.dispatch({
    type: 'UPDATE_ENTRIES',
    entries: [
        {
            type: ['management', 'negative'],
            module: 'Contributions',
            description: 'Deleted type: foobar',
            time: '2018-03-15T14:21:22.736488+00:00',
            userFullName: 'Marco Vidal'
        },
        {
            type: ['management', 'positive'],
            module: 'Contributions',
            description: 'Added type: barfoo',
            time: '2018-03-15T15:20:20.716978+00:00',
            userFullName: 'Pedro Ferreira'
        },
        {
            type: ['management', 'change'],
            module: 'Contributions',
            description: 'Added type: barbarbar',
            time: '2018-03-16T15:20:20.716978+00:00',
            userFullName: 'Michal Kolodziejski'
        }
    ]
});
