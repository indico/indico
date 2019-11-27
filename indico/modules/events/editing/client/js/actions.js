// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editableDetailsURL from 'indico-url:event_editing.api_editable';
import getReviewURL from 'indico-url:event_editing.api_review_editable';

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction, submitFormAction} from 'indico/utils/redux';

export const SET_LOADING = 'SET_LOADING';
export const SET_DETAILS = 'SET_DETAILS';

export function loadTimeline(eventId, contributionId, type) {
  const url = editableDetailsURL({confId: eventId, contrib_id: contributionId, type});
  return ajaxAction(() => indicoAxios.get(url), SET_LOADING, SET_DETAILS);
}

export function reviewEditable(eventId, contributionId, type, revision, formData) {
  const url = getReviewURL({
    confId: eventId,
    contrib_id: contributionId,
    type,
    revision_id: revision.id,
  });

  return submitFormAction(() => indicoAxios.post(url, formData), null, () =>
    loadTimeline(eventId, contributionId, type)
  );
}
