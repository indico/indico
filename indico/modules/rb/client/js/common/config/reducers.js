// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {combineReducers} from 'redux';

import {camelizeKeys} from 'indico/utils/case';
import {requestReducer} from 'indico/utils/redux';

import {actions as adminActions} from '../../modules/admin';

import * as configActions from './actions';

export const initialState = {
  roomsSpriteToken: '',
  languages: {},
  tileServerURL: '',
  gracePeriod: 1,
  helpURL: '',
  hasTOS: false,
  tosHTML: null,
  hasPrivacyPolicy: false,
  privacyPolicyHTML: null,
  contactEmail: null,
};

export default combineReducers({
  request: requestReducer(
    configActions.FETCH_REQUEST,
    configActions.FETCH_SUCCESS,
    configActions.FETCH_ERROR
  ),
  data: (state = initialState, action) => {
    switch (action.type) {
      case configActions.CONFIG_RECEIVED: {
        const {
          roomsSpriteToken,
          gracePeriod,
          managersEditRooms,
          helpURL,
          contactEmail,
          hasPrivacyPolicy,
          hasTos: hasTOS,
          tosHtml: tosHTML,
          privacyPolicyHtml: privacyPolicyHTML,
          tileserverURL: tileServerURL,
        } = camelizeKeys(action.data);
        const {languages} = action.data;
        return {
          roomsSpriteToken,
          languages,
          tileServerURL,
          gracePeriod,
          managersEditRooms,
          helpURL,
          hasTOS,
          tosHTML,
          hasPrivacyPolicy,
          privacyPolicyHTML,
          contactEmail,
        };
      }
      case adminActions.SETTINGS_RECEIVED:
        return {...state, tileServerURL: action.data.tileserver_url};
      case configActions.SET_ROOMS_SPRITE_TOKEN:
        return {...state, roomsSpriteToken: action.token};
      default:
        return state;
    }
  },
});
