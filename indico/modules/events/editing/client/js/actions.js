// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction, submitFormAction} from 'indico/utils/redux';

import {getStaticData} from './selectors';

export const SET_LOADING = 'SET_LOADING';
export const SET_DETAILS = 'SET_DETAILS';

export function loadTimeline() {
  return async (dispatch, getStore) => {
    const {editableDetailsURL: url} = getStaticData(getStore());
    return await ajaxAction(() => indicoAxios.get(url), SET_LOADING, SET_DETAILS)(dispatch);
  };
}

export function reviewEditable(revision, formData) {
  return submitFormAction(() => indicoAxios.post(revision.reviewURL, formData), null, () =>
    loadTimeline()
  );
}

export function confirmEditableChanges(revision, formData) {
  return submitFormAction(() => indicoAxios.post(revision.confirmURL, formData), null, () =>
    loadTimeline()
  );
}

export function createRevisionComment(url, formData) {
  return submitFormAction(() => indicoAxios.post(url, formData), null, () => loadTimeline());
}

export function deleteRevisionComment(url) {
  return ajaxAction(() => indicoAxios.delete(url), null, () => loadTimeline());
}

export function createRevision(url, files) {
  return ajaxAction(() => indicoAxios.post(url, files), null, () => loadTimeline());
}
