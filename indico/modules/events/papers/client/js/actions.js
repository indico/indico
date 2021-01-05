// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import commentActionsURL from 'indico-url:papers.api_comment_actions';
import createCommentURL from 'indico-url:papers.api_create_comment';
import createReviewURL from 'indico-url:papers.api_create_review';
import judgePaperURL from 'indico-url:papers.api_judge_paper';
import paperInfoURL from 'indico-url:papers.api_paper_details';
import resetPaperStateURL from 'indico-url:papers.api_reset_paper_state';
import updateReviewURL from 'indico-url:papers.api_update_review';

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction, submitFormAction} from 'indico/utils/redux';

export const FETCH_PAPER_DETAILS_REQUEST = 'papers/FETCH_PAPER_DETAILS_REQUEST';
export const FETCH_PAPER_DETAILS_SUCCESS = 'papers/FETCH_PAPER_DETAILS_SUCCESS';
export const FETCH_PAPER_DETAILS_ERROR = 'papers/FETCH_PAPER_DETAILS_ERROR';

export const RESET_PAPER_JUDGMENT_REQUEST = 'papers/RESET_PAPER_JUDGMENT_REQUEST';
export const RESET_PAPER_JUDGMENT_SUCCESS = 'papers/RESET_PAPER_JUDGMENT_SUCCESS';
export const RESET_PAPER_JUDGMENT_ERROR = 'papers/RESET_PAPER_JUDGMENT_ERROR';

export const DELETE_COMMENT_REQUEST = 'papers/DELETE_COMMENT_REQUEST';
export const DELETE_COMMENT_SUCCESS = 'papers/DELETE_COMMENT_SUCCESS';
export const DELETE_COMMENT_ERROR = 'papers/DELETE_COMMENT_ERROR';

export function fetchPaperDetails(eventId, contributionId) {
  return ajaxAction(
    () => indicoAxios.get(paperInfoURL({confId: eventId, contrib_id: contributionId})),
    FETCH_PAPER_DETAILS_REQUEST,
    FETCH_PAPER_DETAILS_SUCCESS,
    FETCH_PAPER_DETAILS_ERROR
  );
}

export function resetPaperJudgment(eventId, contributionId) {
  return ajaxAction(
    () => indicoAxios.delete(resetPaperStateURL({confId: eventId, contrib_id: contributionId})),
    RESET_PAPER_JUDGMENT_REQUEST,
    [RESET_PAPER_JUDGMENT_SUCCESS, () => fetchPaperDetails(eventId, contributionId)],
    RESET_PAPER_JUDGMENT_ERROR
  );
}

export function createComment(eventId, contributionId, commentData) {
  const params = {
    confId: eventId,
    contrib_id: contributionId,
  };

  return submitFormAction(
    () => indicoAxios.post(createCommentURL(params), commentData),
    null,
    () => fetchPaperDetails(eventId, contributionId),
    null
  );
}

export function updateComment(eventId, contributionId, revisionId, commentId, commentData) {
  const params = {
    confId: eventId,
    contrib_id: contributionId,
    revision_id: revisionId,
    comment_id: commentId,
  };

  return submitFormAction(
    () => indicoAxios.patch(commentActionsURL(params), commentData),
    null,
    () => fetchPaperDetails(eventId, contributionId),
    null
  );
}

export function deleteComment(eventId, contributionId, revisionId, commentId) {
  const params = {
    confId: eventId,
    contrib_id: contributionId,
    revision_id: revisionId,
    comment_id: commentId,
  };
  return ajaxAction(
    () => indicoAxios.delete(commentActionsURL(params)),
    DELETE_COMMENT_REQUEST,
    [DELETE_COMMENT_SUCCESS, () => fetchPaperDetails(eventId, contributionId)],
    DELETE_COMMENT_ERROR,
    data => ({commentId, ...data})
  );
}

export function judgePaper(eventId, contributionId, judgmentData) {
  return submitFormAction(
    () =>
      indicoAxios.post(judgePaperURL({confId: eventId, contrib_id: contributionId}), judgmentData),
    null,
    () => fetchPaperDetails(eventId, contributionId),
    null
  );
}

export function createReview(eventId, contributionId, group, reviewData) {
  return submitFormAction(
    () =>
      indicoAxios.post(
        createReviewURL({confId: eventId, contrib_id: contributionId, review_type: group}),
        reviewData
      ),
    null,
    () => fetchPaperDetails(eventId, contributionId),
    null
  );
}

export function updateReview(eventId, contributionId, revisionId, reviewId, reviewData) {
  return submitFormAction(
    () =>
      indicoAxios.post(
        updateReviewURL({
          confId: eventId,
          contrib_id: contributionId,
          revision_id: revisionId,
          review_id: reviewId,
        }),
        reviewData
      ),
    null,
    () => fetchPaperDetails(eventId, contributionId),
    null
  );
}
