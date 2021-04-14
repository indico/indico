// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {push} from 'connected-react-router';
import qs from 'qs';

import {history} from './history';

// Page state
export const INIT = 'INIT';
export const RESET_PAGE_STATE = 'RESET_PAGE_STATE';

export function init() {
  return {type: INIT};
}

export function resetPageState(namespace) {
  return {type: RESET_PAGE_STATE, namespace};
}

/**
 * Open a history-friendly modal, by setting the corresponding query string.
 *
 * @param {String} name - the name of the modal (e.g. 'room-details')
 * @param {String} value - a value to pass (normally an ID, e.g. room ID)
 * @param {Object} payload - additional information to pass as JSON
 * @param {Boolean} resetHistory - whether to erase any previous 'modal' path segments
 */
export function openModal(
  name,
  value = null,
  payload = null,
  resetHistory = false,
  overridePath = null
) {
  let data = name;
  if (value !== null) {
    data += `:${value}`;
    if (payload !== null) {
      data += `:${JSON.stringify(payload)}`;
    }
  }

  const {
    location: {pathname: path, search: queryString},
  } = history;
  const qsData = queryString ? qs.parse(queryString.slice(1)) : {};
  if (resetHistory || !qsData.modal) {
    // if resetHistory was set, erase other 'modal' path segments
    qsData.modal = [];
  } else if (typeof qsData.modal === 'string') {
    qsData.modal = [qsData.modal];
  }
  qsData.modal.push(data);

  const serializedQs = qs.stringify(qsData, {allowDots: true, arrayFormat: 'repeat'});
  return push((overridePath || path) + (qsData ? `?${serializedQs}` : ''));
}
