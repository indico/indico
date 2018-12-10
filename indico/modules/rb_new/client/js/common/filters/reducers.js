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

import * as globalActions from '../../actions';
import * as filtersActions from './actions';


export function filterReducerFactory(namespace, initialState, postprocess = x => x) {
    let factory;
    if (typeof initialState === 'function') {
        factory = initialState;
    } else {
        factory = () => initialState;
    }
    return (state = factory(namespace), action) => {
        switch (action.type) {
            case filtersActions.SET_FILTER_PARAMETER:
                return action.namespace === namespace
                    ? postprocess({...state, [action.param]: action.data}, action.param)
                    : state;
            case filtersActions.SET_FILTERS:
                if (action.namespace !== namespace) {
                    return state;
                } else if (action.merge) {
                    return {...state, ...action.params};
                } else {
                    return {...factory(namespace), ...action.params};
                }
            case globalActions.RESET_PAGE_STATE:
                return (!action.namespace || action.namespace === namespace) ? factory(namespace) : state;
            default:
                return state;
        }
    };
}
