// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {combineReducers} from 'redux';

import {requestReducer} from 'indico/utils/redux';

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
      case actions.ALL_ROOM_PERMISSIONS_RECEIVED:
        return action.data;
      case actions.ROOM_PERMISSIONS_RECEIVED: {
        const {id, user, admin} = action.data;
        return {
          admin: state.admin ? {...state.admin, [id]: admin} : null,
          user: {...state.user, [id]: user},
        };
      }
      default:
        return state;
    }
  },
});
