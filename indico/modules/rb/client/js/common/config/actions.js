// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fetchConfigURL from 'indico-url:rb.config';

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';

export const FETCH_REQUEST = 'config/FETCH_REQUEST';
export const FETCH_SUCCESS = 'config/FETCH_SUCCESS';
export const FETCH_ERROR = 'config/FETCH_ERROR';
export const CONFIG_RECEIVED = 'config/CONFIG_RECEIVED';
export const SET_ROOMS_SPRITE_TOKEN = 'config/SET_ROOMS_SPRITE_TOKEN';

export function fetchConfig() {
  return ajaxAction(
    () => indicoAxios.get(fetchConfigURL()),
    FETCH_REQUEST,
    [CONFIG_RECEIVED, FETCH_SUCCESS],
    [FETCH_ERROR]
  );
}

export function setRoomsSpriteToken(token) {
  return {
    type: SET_ROOMS_SPRITE_TOKEN,
    token,
  };
}
