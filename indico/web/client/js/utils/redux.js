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
import {composeWithDevTools} from 'redux-devtools-extension';


// similar to the standard combineReducers, but accepts
// root reducers as well
export function combineRootReducers(...reducers) {
    const reducerFunctions = reducers.map(reducer => (
        (typeof reducer === 'function') ? reducer : combineReducers(reducer))
    );

    return (state, action) => reducerFunctions.reduce((st, fn) => fn(st, action), state);
}

export default function createReduxStore(
    name, reducers, initialData = {}, additionalMiddleware = [], postReducers = [], enhancer = r => r
) {
    const middleware = [thunkMiddleware, ...additionalMiddleware];
    const composeEnhancers = composeWithDevTools({name: `Indico:${name}`});

    return createStore(
        enhancer(combineRootReducers({
            staticData: (state = {}) => state,
            ...reducers
        }, ...postReducers)),
        initialData,
        composeEnhancers(applyMiddleware(...middleware)));
}
