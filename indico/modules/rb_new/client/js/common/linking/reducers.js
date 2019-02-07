/* This file is part of Indico.
 * Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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

import * as linkingActions from './actions';
import {actions as bookRoomActions} from '../../modules/bookRoom';


const initialState = {
    type: null,
    id: null,
    title: null,
    eventURL: null,
    eventTitle: null,
    ownRoomId: null,
    ownRoomName: null,
};

export default (state = initialState, action) => {
    switch (action.type) {
        case linkingActions.SET_OBJECT:
            return {
                type: action.objectType,
                id: action.objectId,
                title: action.objectTitle,
                eventURL: action.eventURL,
                eventTitle: action.eventTitle,
                ownRoomId: action.ownRoomId,
                ownRoomName: action.ownRoomName,
            };
        case linkingActions.CLEAR_OBJECT:
        case bookRoomActions.CREATE_BOOKING_SUCCESS:
            return initialState;
        default:
            return state;
    }
};
