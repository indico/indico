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

import {combineReducers} from 'redux';

import {requestReducer} from 'indico/utils/redux';
import camelizeKeys from 'indico/utils/camelize';
import filterReducerFactory from '../../reducers/roomBooking/filters';
import * as blockingsActions from './actions';


export const initialFilterStateFactory = () => ({
    myBlockings: false,
    myRooms: false,
    timeframe: 'recent'
});

export default combineReducers({
    requests: combineReducers({
        blockings: requestReducer(
            blockingsActions.FETCH_BLOCKINGS_REQUEST,
            blockingsActions.FETCH_BLOCKINGS_SUCCESS,
            blockingsActions.FETCH_BLOCKINGS_ERROR
        ),
        create: requestReducer(
            blockingsActions.CREATE_BLOCKING_REQUEST,
            blockingsActions.CREATE_BLOCKING_SUCCESS,
            blockingsActions.CREATE_BLOCKING_ERROR
        ),
    }),
    blockings: (state = [], action) => {
        switch (action.type) {
            case blockingsActions.BLOCKINGS_RECEIVED:
                return action.data.map((blocking) => camelizeKeys(blocking));
            default:
                return state;
        }
    },
    filters: filterReducerFactory(blockingsActions.FILTER_NAMESPACE, initialFilterStateFactory),
});
