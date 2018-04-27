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

import {createStore, combineReducers, applyMiddleware} from 'redux';
import thunkMiddleware from 'redux-thunk';
import loggerMiddleware from 'redux-logger';
import {composeWithDevTools} from 'redux-devtools-extension';


// similar to the standard combineReducers, but accepts
// root reducers as well
function _combineReducers(...reducers) {
    return (state, action) => {
        for (const reducer of reducers) {
            if (typeof reducer === 'function') {
                // it's a reducer
                state = reducer(state, action);
            } else {
                state = combineReducers(reducer)(state, action);
            }
        }
        return state;
    };
}


export default function createReduxStore(reducers, initialData = {}, additionalMiddleware = [], postReducers = []) {
    const middleware = [thunkMiddleware, ...additionalMiddleware];
    if (process.env.NODE_ENV === 'development') {
        middleware.push(loggerMiddleware);
    }
    const enhancer = composeWithDevTools(applyMiddleware(...middleware));

    return createStore(
        _combineReducers({
            staticData: (state = {}) => state,
            ...reducers
        }, ...postReducers),
        initialData,
        enhancer);
}
