// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import categoryAddFieldURL from 'indico-url:categories.add_field';
import categoryAddSectionURL from 'indico-url:categories.add_section';
import categoryAddTextURL from 'indico-url:categories.add_text';
import categoryModifyFieldURL from 'indico-url:categories.modify_field';
import categoryModifySectionURL from 'indico-url:categories.modify_section';
import categoryModifyTextURL from 'indico-url:categories.modify_text';
import categoryMoveFieldURL from 'indico-url:categories.move_field';
import categoryMoveSectionURL from 'indico-url:categories.move_section';
import categoryMoveTextURL from 'indico-url:categories.move_text';
import categoryToggleFieldURL from 'indico-url:categories.toggle_field';
import categoryToggleSectionURL from 'indico-url:categories.toggle_section';
import categoryToggleTextURL from 'indico-url:categories.toggle_text';
import eventAddFieldURL from 'indico-url:event_registration.add_field';
import eventAddSectionURL from 'indico-url:event_registration.add_section';
import eventAddTextURL from 'indico-url:event_registration.add_text';
import eventModifyFieldURL from 'indico-url:event_registration.modify_field';
import eventModifySectionURL from 'indico-url:event_registration.modify_section';
import eventModifyTextURL from 'indico-url:event_registration.modify_text';
import eventMoveFieldURL from 'indico-url:event_registration.move_field';
import eventMoveSectionURL from 'indico-url:event_registration.move_section';
import eventMoveTextURL from 'indico-url:event_registration.move_text';
import eventToggleFieldURL from 'indico-url:event_registration.toggle_field';
import eventToggleSectionURL from 'indico-url:event_registration.toggle_section';
import eventToggleTextURL from 'indico-url:event_registration.toggle_text';

import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';
import {ajaxAction, submitFormAction} from 'indico/utils/redux';

import {getSectionIdForItem, getURLParams, getURLFromTarget, pickItemURL} from './selectors';

export const LOCK_UI = 'Lock interface';
export const UNLOCK_UI = 'Unlock interface';
export const SET_FORM_DATA = 'Set form data';
export const MOVE_SECTION = 'Move section';
export const UPDATE_SECTION = 'Update section';
export const TOGGLE_SECTION = 'Toggle section';
export const REMOVE_SECTION = 'Remove section';
export const CREATE_SECTION = 'Create section';
export const MOVE_ITEM = 'Move item';
export const UPDATE_ITEM = 'Update item';
export const REMOVE_ITEM = 'Remove item';
export const CREATE_ITEM = 'Create item';
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

// TODO: remove patch mode unless we end up using it
function _updateSection(sectionId, data, patch = false) {
  return {type: UPDATE_SECTION, sectionId, data, patch};
}

function _createSection(data) {
  return {type: CREATE_SECTION, data};
}

export function moveItem(sectionId, sourceIndex, targetIndex) {
  return {type: MOVE_ITEM, sectionId, sourceIndex, targetIndex};
}

function _updateItem(itemId, data) {
  return {type: UPDATE_ITEM, itemId, data};
}

function _removeItem(itemId) {
  return {type: REMOVE_ITEM, itemId};
}

function _createItem(data) {
  return {type: CREATE_ITEM, data};
}

export function saveSectionPosition(sectionId, position, oldPosition) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const url = getURLFromTarget(store)(eventMoveSectionURL, categoryMoveSectionURL)(
      getURLParams(store)(sectionId)
    );
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
    const url = getURLFromTarget(store)(eventToggleSectionURL, categoryToggleSectionURL)({
      ...params,
      enable: 'true',
    });
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
    const url = getURLFromTarget(store)(eventToggleSectionURL, categoryToggleSectionURL)({
      ...params,
      enable: 'false',
    });
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
    const url = getURLFromTarget(store)(eventModifySectionURL, categoryModifySectionURL)(
      getURLParams(store)(sectionId)
    );
    const resp = await lockingAjaxAction(() => indicoAxios.delete(url))(dispatch);
    if (!resp.error) {
      dispatch(_removeSection(sectionId));
    }
    return !!resp.error;
  };
}

export function updateSection(sectionId, data) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const url = getURLFromTarget(store)(eventModifySectionURL, categoryModifySectionURL)(
      getURLParams(store)(sectionId)
    );
    const payload = {changes: data};
    const resp = await submitFormAction(() => indicoAxios.patch(url, payload))(dispatch);
    if (!resp.error) {
      delete resp.data.items;
      dispatch(_updateSection(sectionId, resp.data));
    }
    return camelizeKeys(resp);
  };
}

export function createSection(data) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const url = getURLFromTarget(store)(eventAddSectionURL, categoryAddSectionURL)(
      getURLParams(store)()
    );
    const resp = await submitFormAction(() => indicoAxios.post(url, data))(dispatch);
    if (!resp.error) {
      delete resp.data.items;
      dispatch(_createSection(resp.data));
    }
    return camelizeKeys(resp);
  };
}

export function saveItemPosition(sectionId, itemId, position, oldPosition) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const urlFunc = pickItemURL(store, itemId)(
      getURLFromTarget(store)(eventMoveTextURL, categoryMoveTextURL),
      getURLFromTarget(store)(eventMoveFieldURL, categoryMoveFieldURL)
    );
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
    const urlFunc = pickItemURL(store, itemId)(
      getURLFromTarget(store)(eventToggleTextURL, categoryToggleTextURL),
      getURLFromTarget(store)(eventToggleFieldURL, categoryToggleFieldURL)
    );
    const params = getURLParams(store)(sectionId, itemId);
    const url = urlFunc({...params, enable: 'true'});
    const resp = await lockingAjaxAction(() => indicoAxios.post(url))(dispatch);
    if (!resp.error) {
      dispatch(_updateItem(itemId, resp.data.view_data));
      dispatch(updatePositions(resp.data.positions));
    }
  };
}

export function disableItem(itemId) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const sectionId = getSectionIdForItem(store, itemId);
    const urlFunc = pickItemURL(store, itemId)(
      getURLFromTarget(store)(eventToggleTextURL, categoryToggleTextURL),
      getURLFromTarget(store)(eventToggleFieldURL, categoryToggleFieldURL)
    );
    const params = getURLParams(store)(sectionId, itemId);
    const url = urlFunc({...params, enable: 'false'});
    const resp = await lockingAjaxAction(() => indicoAxios.post(url))(dispatch);
    if (!resp.error) {
      dispatch(_updateItem(itemId, resp.data.view_data));
      dispatch(updatePositions(resp.data.positions));
    }
  };
}

export function removeItem(itemId) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const sectionId = getSectionIdForItem(store, itemId);
    const urlFunc = pickItemURL(store, itemId)(
      getURLFromTarget(store)(eventModifyTextURL, categoryModifyTextURL),
      getURLFromTarget(store)(eventModifyFieldURL, categoryModifyFieldURL)
    );
    const url = urlFunc(getURLParams(store)(sectionId, itemId));
    const resp = await lockingAjaxAction(() => indicoAxios.delete(url))(dispatch);
    if (!resp.error) {
      dispatch(_removeItem(itemId));
    }
    return !!resp.error;
  };
}

export function updateItem(itemId, data) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const sectionId = getSectionIdForItem(store, itemId);
    const urlFunc = pickItemURL(store, itemId)(
      getURLFromTarget(store)(eventModifyTextURL, categoryModifyTextURL),
      getURLFromTarget(store)(eventModifyFieldURL, categoryModifyFieldURL)
    );
    const url = urlFunc(getURLParams(store)(sectionId, itemId));
    const payload = {fieldData: data};
    const resp = await submitFormAction(() => indicoAxios.patch(url, payload))(dispatch);
    if (!resp.error) {
      dispatch(_updateItem(itemId, resp.data.view_data));
    }
    return camelizeKeys(resp);
  };
}

export function createItem(sectionId, inputType, data) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const urlFunc =
      inputType === 'label'
        ? getURLFromTarget(store)(eventAddTextURL, categoryAddTextURL)
        : getURLFromTarget(store)(eventAddFieldURL, categoryAddFieldURL);
    const url = urlFunc(getURLParams(store)(sectionId));
    const payload = {fieldData: {...data, input_type: inputType}};
    const resp = await submitFormAction(() => indicoAxios.post(url, payload))(dispatch);
    if (!resp.error) {
      dispatch(_createItem(resp.data.view_data));
    }
    return camelizeKeys(resp);
  };
}
