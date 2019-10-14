// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import paperInfoURL from 'indico-url:papers_api.paper_details';
import resetPaperStateURL from 'indico-url:papers_api.reset_paper_state';
import paperPermissionsURL from 'indico-url:papers_api.paper_permissions';
import deleteCommentURL from 'indico-url:papers_api.delete_comment';
import judgePaperURL from 'indico-url:papers_api.judge_paper';

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';

export const FETCH_PAPER_DETAILS_REQUEST = 'papers/FETCH_PAPER_DETAILS_REQUEST';
export const FETCH_PAPER_DETAILS_SUCCESS = 'papers/FETCH_PAPER_DETAILS_SUCCESS';
export const FETCH_PAPER_DETAILS_ERROR = 'papers/FETCH_PAPER_DETAILS_ERROR';

export const FETCH_PAPER_PERMISSIONS_REQUEST = 'papers/FETCH_PAPER_PERMISSIONS_REQUEST';
export const FETCH_PAPER_PERMISSIONS_SUCCESS = 'papers/FETCH_PAPER_PERMISSIONS_SUCCESS';
export const FETCH_PAPER_PERMISSIONS_ERROR = 'papers/FETCH_PAPER_PERMISSIONS_ERROR';

export const RESET_PAPER_JUDGMENT_REQUEST = 'papers/RESET_PAPER_JUDGMENT_REQUEST';
export const RESET_PAPER_JUDGMENT_SUCCESS = 'papers/RESET_PAPER_JUDGMENT_SUCCESS';
export const RESET_PAPER_JUDGMENT_ERROR = 'papers/RESET_PAPER_JUDGMENT_ERROR';

export const DELETE_COMMENT_REQUEST = 'papers/DELETE_COMMENT_REQUEST';
export const DELETE_COMMENT_SUCCESS = 'papers/DELETE_COMMENT_SUCCESS';
export const DELETE_COMMENT_ERROR = 'papers/DELETE_COMMENT_ERROR';

export const JUDGE_PAPER_REQUEST = 'papers/JUDGE_PAPER_REQUEST';
export const JUDGE_PAPER_SUCCESS = 'papers/JUDGE_PAPER_SUCCESS';
export const JUDGE_PAPER_ERROR = 'papers/JUDGE_PAPER_ERROR';

export function fetchPaperDetails(confId, contributionId) {
  return ajaxAction(
    () => indicoAxios.get(paperInfoURL({confId, contrib_id: contributionId})),
    FETCH_PAPER_DETAILS_REQUEST,
    FETCH_PAPER_DETAILS_SUCCESS,
    FETCH_PAPER_DETAILS_ERROR
  );
}

export function fetchPaperPermissions(confId, contributionId) {
  return ajaxAction(
    () => indicoAxios.get(paperPermissionsURL({confId, contrib_id: contributionId})),
    FETCH_PAPER_PERMISSIONS_REQUEST,
    FETCH_PAPER_PERMISSIONS_SUCCESS,
    FETCH_PAPER_PERMISSIONS_ERROR
  );
}

export function resetPaperJudgment(confId, contributionId) {
  return ajaxAction(
    () => indicoAxios.delete(resetPaperStateURL({confId, contrib_id: contributionId})),
    RESET_PAPER_JUDGMENT_REQUEST,
    RESET_PAPER_JUDGMENT_SUCCESS,
    RESET_PAPER_JUDGMENT_ERROR
  );
}

export function deleteComment(confId, contributionId, revisionId, commentId) {
  const params = {
    confId,
    contrib_id: contributionId,
    revision_id: revisionId,
    comment_id: commentId,
  };
  return ajaxAction(
    () => indicoAxios.delete(deleteCommentURL(params)),
    DELETE_COMMENT_REQUEST,
    DELETE_COMMENT_SUCCESS,
    DELETE_COMMENT_ERROR,
    data => ({commentId, paper: data})
  );
}

export function judgePaper(confId, contributionId, judgmentData) {
  return ajaxAction(
    () => indicoAxios.post(judgePaperURL({confId, contrib_id: contributionId}), judgmentData),
    JUDGE_PAPER_REQUEST,
    JUDGE_PAPER_SUCCESS,
    JUDGE_PAPER_ERROR
  );
}
