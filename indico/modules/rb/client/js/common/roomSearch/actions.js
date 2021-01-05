// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import searchRoomsURL from 'indico-url:rb.search_rooms';

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';

import {selectors as userSelectors} from '../../common/user';
import {preProcessParameters} from '../../util';
import {validateFilters} from '../filters';

import {ajax as ajaxFilterRules} from './serializers';

export function roomSearchActionsFactory(namespace) {
  const SEARCH_RESULTS_RECEIVED = `${namespace}/SEARCH_RESULTS_RECEIVED`;
  const SEARCH_ROOMS_REQUEST = `${namespace}/SEARCH_ROOMS_REQUEST`;
  const SEARCH_ROOMS_SUCCESS = `${namespace}/SEARCH_ROOMS_SUCCESS`;
  const SEARCH_ROOMS_ERROR = `${namespace}/SEARCH_ROOMS_ERROR`;

  function searchRooms() {
    return async (dispatch, getStore) => {
      const store = getStore();
      const {filters} = store[namespace];
      if (!validateFilters(filters, namespace, dispatch)) {
        return;
      }
      const params = preProcessParameters(filters, ajaxFilterRules);
      if (namespace === 'bookRoom' && userSelectors.isUserAdminOverrideEnabled(store)) {
        params.admin_override_enabled = true;
      }
      return await ajaxAction(
        () => indicoAxios.get(searchRoomsURL(), {params}),
        SEARCH_ROOMS_REQUEST,
        [SEARCH_RESULTS_RECEIVED, SEARCH_ROOMS_SUCCESS],
        SEARCH_ROOMS_ERROR
      )(dispatch);
    };
  }

  return {
    SEARCH_RESULTS_RECEIVED,
    SEARCH_ROOMS_REQUEST,
    SEARCH_ROOMS_SUCCESS,
    SEARCH_ROOMS_ERROR,
    searchRooms,
  };
}
