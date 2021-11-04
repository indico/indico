// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moveFieldURL from 'indico-url:event_registration.move_field';
import moveSectionURL from 'indico-url:event_registration.move_section';
import moveTextURL from 'indico-url:event_registration.move_text';

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';

export const LOCK_UI = 'Lock interface';
export const UNLOCK_UI = 'Unlock interface';
export const MOVE_SECTION = 'Move section';
export const MOVE_ITEM = 'Move item';

function lockUI() {
  return {type: LOCK_UI};
}

function unlockUI() {
  return {type: UNLOCK_UI};
}

function lockingAjaxAction(requestFunc, ...args) {
  const fn = ajaxAction(requestFunc, ...args);
  return async dispatch => {
    dispatch(lockUI());
    const resp = await fn();
    dispatch(unlockUI());
    return resp;
  };
}

export function moveSection(sourceIndex, targetIndex) {
  return {type: MOVE_SECTION, sourceIndex, targetIndex};
}

export function moveItem(sectionId, sourceIndex, targetIndex) {
  return {type: MOVE_ITEM, sectionId, sourceIndex, targetIndex};
}

export function saveSectionPosition(sectionId, position, oldPosition) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const eventId = store.staticData.eventId;
    const regformId = store.staticData.regformId;
    const resp = await lockingAjaxAction(() =>
      indicoAxios.post(
        moveSectionURL({event_id: eventId, reg_form_id: regformId, section_id: sectionId}),
        {endPos: position}
      )
    )(dispatch);
    if (resp.error) {
      // XXX alternatively we could keep the UI locked and require a refresh after
      // a failure to make sure we are in a fully consistent state...
      // but moving stuff around is the only case where the local state gets updated
      // before saving, so it's probably not worth it
      dispatch(moveSection(position, oldPosition));
    }
  };
}

export function saveItemPosition(sectionId, itemId, position, oldPosition, isStaticText) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const eventId = store.staticData.eventId;
    const regformId = store.staticData.regformId;
    const urlFunc = isStaticText ? moveTextURL : moveFieldURL;
    const resp = await lockingAjaxAction(() =>
      indicoAxios.post(
        urlFunc({
          event_id: eventId,
          reg_form_id: regformId,
          section_id: sectionId,
          field_id: itemId,
        }),
        {endPos: position}
      )
    )(dispatch);
    if (resp.error) {
      // XXX alternatively we could keep the UI locked and require a refresh after
      // a failure to make sure we are in a fully consistent state...
      // but moving stuff around is the only case where the local state gets updated
      // before saving, so it's probably not worth it
      dispatch(moveItem(sectionId, position, oldPosition));
    }
  };
}
