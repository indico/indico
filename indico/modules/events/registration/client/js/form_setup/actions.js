// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import modifyFieldURL from 'indico-url:event_registration.modify_field';
import modifySectionURL from 'indico-url:event_registration.modify_section';
import modifyTextURL from 'indico-url:event_registration.modify_text';
import moveFieldURL from 'indico-url:event_registration.move_field';
import moveSectionURL from 'indico-url:event_registration.move_section';
import moveTextURL from 'indico-url:event_registration.move_text';
import toggleFieldURL from 'indico-url:event_registration.toggle_field';
import toggleSectionURL from 'indico-url:event_registration.toggle_section';
import toggleTextURL from 'indico-url:event_registration.toggle_text';

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';

import {getSectionIdForItem, getURLParams, pickItemURL} from './selectors';

export const LOCK_UI = 'Lock interface';
export const UNLOCK_UI = 'Unlock interface';
export const SET_FORM_DATA = 'Set form data';
export const MOVE_SECTION = 'Move section';
export const UPDATE_SECTION = 'Update section';
export const TOGGLE_SECTION = 'Toggle section';
export const REMOVE_SECTION = 'Remove section';
export const MOVE_ITEM = 'Move item';
export const UPDATE_ITEM = 'Update item';
export const REMOVE_ITEM = 'Remove item';
export const UPDATE_POSITIONS = 'Update positions';

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

export function setFormData(data) {
  return {type: SET_FORM_DATA, items: data.items, sections: data.sections};
}

function updatePositions(data) {
  return {type: UPDATE_POSITIONS, items: data.items, sections: data.sections};
}

export function moveSection(sourceIndex, targetIndex) {
  return {type: MOVE_SECTION, sourceIndex, targetIndex};
}

function _toggleSection(sectionId, enabled) {
  return {type: TOGGLE_SECTION, sectionId, enabled};
}

function _removeSection(sectionId) {
  return {type: REMOVE_SECTION, sectionId};
}

// TODO currently unused, but we'll most likely start using it when editing
// sections; otherwise remove it if we don't need it after all.
// eslint-disable-next-line no-unused-vars
function updateSection(sectionId, data, patch = false) {
  return {type: UPDATE_SECTION, sectionId, data, patch};
}

export function moveItem(sectionId, sourceIndex, targetIndex) {
  return {type: MOVE_ITEM, sectionId, sourceIndex, targetIndex};
}

function updateItem(itemId, data) {
  return {type: UPDATE_ITEM, itemId, data};
}

function _removeItem(itemId) {
  return {type: REMOVE_ITEM, itemId};
}

export function saveSectionPosition(sectionId, position, oldPosition) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const url = moveSectionURL(getURLParams(store)(sectionId));
    const resp = await lockingAjaxAction(() => indicoAxios.post(url, {endPos: position}))(dispatch);
    if (resp.error) {
      // XXX alternatively we could keep the UI locked and require a refresh after
      // a failure to make sure we are in a fully consistent state...
      // but moving stuff around is the only case where the local state gets updated
      // before saving, so it's probably not worth it
      dispatch(moveSection(position, oldPosition));
    }
  };
}

export function enableSection(sectionId) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const params = getURLParams(store)(sectionId);
    const url = toggleSectionURL({...params, enable: 'true'});
    const resp = await lockingAjaxAction(() => indicoAxios.post(url))(dispatch);
    if (!resp.error) {
      dispatch(_toggleSection(sectionId, true));
      dispatch(updatePositions(resp.data.positions));
    }
  };
}

export function disableSection(sectionId) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const params = getURLParams(store)(sectionId);
    const url = toggleSectionURL({...params, enable: 'false'});
    const resp = await lockingAjaxAction(() => indicoAxios.post(url))(dispatch);
    if (!resp.error) {
      dispatch(_toggleSection(sectionId, false));
      dispatch(updatePositions(resp.data.positions));
    }
  };
}

export function removeSection(sectionId) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const url = modifySectionURL(getURLParams(store)(sectionId));
    const resp = await lockingAjaxAction(() => indicoAxios.delete(url))(dispatch);
    if (!resp.error) {
      dispatch(_removeSection(sectionId));
    }
  };
}

export function saveItemPosition(sectionId, itemId, position, oldPosition) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const urlFunc = pickItemURL(store, itemId)(moveTextURL, moveFieldURL);
    const url = urlFunc(getURLParams(store)(sectionId, itemId));
    const resp = await lockingAjaxAction(() => indicoAxios.post(url, {endPos: position}))(dispatch);
    if (resp.error) {
      // XXX alternatively we could keep the UI locked and require a refresh after
      // a failure to make sure we are in a fully consistent state...
      // but moving stuff around is the only case where the local state gets updated
      // before saving, so it's probably not worth it
      dispatch(moveItem(sectionId, position, oldPosition));
    }
  };
}

export function enableItem(itemId) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const sectionId = getSectionIdForItem(store, itemId);
    const urlFunc = pickItemURL(store, itemId)(toggleTextURL, toggleFieldURL);
    const params = getURLParams(store)(sectionId, itemId);
    const url = urlFunc({...params, enable: 'true'});
    const resp = await lockingAjaxAction(() => indicoAxios.post(url))(dispatch);
    if (!resp.error) {
      dispatch(updateItem(itemId, resp.data.view_data));
      dispatch(updatePositions(resp.data.positions));
    }
  };
}

export function disableItem(itemId) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const sectionId = getSectionIdForItem(store, itemId);
    const urlFunc = pickItemURL(store, itemId)(toggleTextURL, toggleFieldURL);
    const params = getURLParams(store)(sectionId, itemId);
    const url = urlFunc({...params, enable: 'false'});
    const resp = await lockingAjaxAction(() => indicoAxios.post(url))(dispatch);
    if (!resp.error) {
      dispatch(updateItem(itemId, resp.data.view_data));
      dispatch(updatePositions(resp.data.positions));
    }
  };
}

export function removeItem(itemId) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const sectionId = getSectionIdForItem(store, itemId);
    const urlFunc = pickItemURL(store, itemId)(modifyTextURL, modifyFieldURL);
    const url = urlFunc(getURLParams(store)(sectionId, itemId));
    const resp = await lockingAjaxAction(() => indicoAxios.delete(url))(dispatch);
    if (!resp.error) {
      dispatch(_removeItem(itemId));
    }
  };
}
