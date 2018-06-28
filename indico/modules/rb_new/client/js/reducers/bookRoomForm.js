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
import {actionTypes as reduxFormActions} from 'redux-form';
import * as actions from '../actions';


const initialState = {
    bookingState: {
        ongoing: false,
        success: null
    },
    fields: {
        user: {
            disabled: true
        }
    }
};

export default function reducer(state = initialState, action) {
    // if usage !== 'someone' (=== 'myself'), then we disable the user input
    if (action.type === reduxFormActions.CHANGE && action.meta.field === 'usage') {
        const newState = _.cloneDeep(state);
        _.set(newState, 'fields.user.disabled', action.payload !== 'someone');
        _.set(newState, 'values.user', null);
        return newState;
    }

    const {type, message, isPrebooking} = action;

    switch (type) {
        case actions.BOOKING_ONGOING:
            return {...state, bookingState: {ongoing: true}};
        case actions.BOOKING_CONFIRMED:
            return {...state, bookingState: {ongoing: false, success: true, message: null, isPrebooking}};
        case actions.BOOKING_FAILED:
            return {...state, bookingState: {ongoing: false, success: false, message}};
        case actions.RESET_BOOKING_STATE:
            return {...initialState};
    }
    return state;
}
