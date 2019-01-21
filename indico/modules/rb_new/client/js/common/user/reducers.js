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
import * as actions from './actions';


const initialUserInfoState = {
    firstName: '',
    lastName: '',
    email: '',
    avatarBgColor: '',
    language: '',
    isAdmin: false,
    isRBAdmin: false,
    isAdminOverrideEnabled: false,
    hasOwnedRooms: false,
    favoriteUsers: [],
};

export default combineReducers({
    requests: combineReducers({
        info: requestReducer(
            actions.FETCH_USER_INFO_REQUEST,
            actions.FETCH_USER_INFO_SUCCESS,
            actions.FETCH_USER_INFO_ERROR
        ),
        favorites: requestReducer(
            actions.FETCH_FAVORITES_REQUEST,
            actions.FETCH_FAVORITES_SUCCESS,
            actions.FETCH_FAVORITES_ERROR
        ),
        roomPermissions: requestReducer(
            actions.FETCH_ROOM_PERMISSIONS_REQUEST,
            actions.FETCH_ROOM_PERMISSIONS_SUCCESS,
            actions.FETCH_ROOM_PERMISSIONS_ERROR
        ),
    }),
    info: (state = initialUserInfoState, action) => {
        switch (action.type) {
            case actions.USER_INFO_RECEIVED: {
                const user = action.data;
                return {
                    ...state,
                    id: user.id,
                    identifier: user.identifier,
                    firstName: user.first_name,
                    lastName: user.last_name,
                    fullName: user.full_name,
                    email: user.email,
                    avatarBgColor: user.avatar_bg_color,
                    language: user.language,
                    isAdmin: user.is_admin,
                    isRBAdmin: user.is_rb_admin,
                    hasOwnedRooms: user.has_owned_rooms,
                    favoriteUsers: camelizeKeys(user.favorite_users)
                };
            }
            case actions.TOGGLE_ADMIN_OVERRIDE:
                return {...state, isAdminOverrideEnabled: !state.isAdminOverrideEnabled};
            default:
                return state;
        }
    },
    favorites: (state = {}, action) => {
        switch (action.type) {
            case actions.FAVORITES_RECEIVED:
                return action.data.reduce((obj, id) => ({...obj, [id]: true}), {});
            case actions.ADD_FAVORITE_ROOM:
                return {...state, [action.id]: true};
            case actions.DEL_FAVORITE_ROOM:
                return {...state, [action.id]: false};
            default:
                return state;
        }
    },
    roomPermissions: (state = {admin: null, user: {}}, action) => {
        switch (action.type) {
            case actions.ROOM_PERMISSIONS_RECEIVED:
                return action.data;
            default:
                return state;
        }
    },
});
