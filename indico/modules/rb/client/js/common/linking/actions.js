// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import getLinkedObjectDataURL from 'indico-url:rb.linked_object_data';

import _ from 'lodash';
import qs from 'qs';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

export const SET_OBJECT = 'linking/SET_OBJECT';
export const CLEAR_OBJECT = 'linking/CLEAR_OBJECT';

export function setObjectFromURL(queryString) {
  return async dispatch => {
    const {linkType, linkId} = camelizeKeys(qs.parse(queryString));
    if (linkType === undefined || linkId === undefined) {
      return;
    }

    let response;
    try {
      response = await indicoAxios.get(
        getLinkedObjectDataURL({type: _.snakeCase(linkType), id: linkId})
      );
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    const data = camelizeKeys(response.data);
    if (!data.canAccess) {
      return;
    }
    dispatch({
      type: SET_OBJECT,
      objectType: _.camelCase(linkType),
      objectId: +linkId,
      objectTitle: data.title,
      eventURL: data.eventURL,
      eventTitle: data.eventTitle,
      ownRoomId: data.ownRoomId,
      ownRoomName: data.ownRoomName,
    });
  };
}

export function clearObject() {
  return {type: CLEAR_OBJECT};
}
