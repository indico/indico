// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createSelector} from 'reselect';

import {EditableState, RevisionType} from '../../models';

export const getDetails = state => (state.timeline ? state.timeline.details : null);
export const getNewDetails = state => (state.timeline ? state.timeline.newDetails : null);
export const isInitialEditableDetailsLoading = state =>
  state.timeline.loading && !state.timeline.details;
export const isTimelineOutdated = createSelector(
  getDetails,
  getNewDetails,
  (details, newDetails) => newDetails !== null && !_.isEqual(details, newDetails)
);
export const getEditableState = createSelector(
  getDetails,
  details => details?.state
);
export const getTimelineBlocks = state => state.timeline.timelineBlocks;
export const getLastTimelineBlock = createSelector(
  getTimelineBlocks,
  blocks => blocks && blocks[blocks.length - 1]
);
export const getValidTimelineBlocks = state =>
  state.timeline.timelineBlocks.filter(({isUndone}) => !isUndone);
export const getLastValidTimelineBlock = createSelector(
  getValidTimelineBlocks,
  blocks => blocks && blocks[blocks.length - 1]
);
export const getLastTimelineBlockWithFiles = createSelector(
  getValidTimelineBlocks,
  blocks =>
    blocks &&
    blocks
      .slice()
      .reverse()
      .find(block => block.files.length)
);
export const getValidRevisions = createSelector(
  getDetails,
  details => details?.revisions.filter(({isUndone}) => !isUndone)
);
export const getLastRevision = createSelector(
  getValidRevisions,
  revisions => revisions && revisions[revisions.length - 1]
);
export const getLastRevisionWithFiles = createSelector(
  getValidRevisions,
  revisions =>
    revisions &&
    revisions
      .slice()
      .reverse()
      .find(revision => revision.files.length)
);
export const canReviewLastRevision = createSelector(
  getLastRevision,
  lastRevision => lastRevision && lastRevision.type.name === RevisionType.ready_for_review
);
export const needsSubmitterChanges = createSelector(
  getEditableState,
  state => state?.name === EditableState.needs_submitter_changes
);
export const needsSubmitterConfirmation = createSelector(
  getLastRevision,
  lastRevision =>
    lastRevision && lastRevision.type.name === RevisionType.needs_submitter_confirmation
);
export const getStaticData = state => state.staticData;

export const getNonSystemTags = createSelector(
  getStaticData,
  staticData => staticData.tags.filter(t => !t.system)
);

export const getFileTypes = createSelector(
  getDetails,
  getStaticData,
  (details, staticData) => {
    return staticData.fileTypes.map(fileType => {
      if (!fileType.filenameTemplate) {
        return fileType;
      }
      return {
        ...fileType,
        filenameTemplate: fileType.filenameTemplate.replace(
          '{code}',
          details ? details.contribution.code : staticData.contributionCode
        ),
      };
    });
  }
);

export const getPublishableFileTypes = createSelector(
  getFileTypes,
  fileTypes => fileTypes.filter(ft => ft.publishable)
);

export const hasPublishableFiles = createSelector(
  getPublishableFileTypes,
  getLastRevisionWithFiles,
  (publishableFileTypes, revision) => {
    const usedFileTypes = new Set(revision.files.map(f => f.fileType));
    return publishableFileTypes.some(ft => usedFileTypes.has(ft.id));
  }
);

export const canPerformSubmitterActions = createSelector(
  getDetails,
  details => details?.canPerformSubmitterActions
);

export const canPerformEditorActions = createSelector(
  getDetails,
  details => details?.canPerformEditorActions
);

export const canDeleteEditable = createSelector(
  getDetails,
  details => details?.canDelete
);

export const editingEnabled = createSelector(
  getDetails,
  details => details?.editingEnabled
);

export const canJudgeLastRevision = createSelector(
  getEditableState,
  canPerformEditorActions,
  (state, allowed) => allowed && state?.name === EditableState.ready_for_review
);

export const canEditLastRevision = createSelector(
  getLastRevision,
  canPerformEditorActions,
  (latestRevision, allowed) =>
    allowed &&
    latestRevision &&
    ![RevisionType.new, RevisionType.ready_for_review, RevisionType.reset].includes(
      latestRevision.type.name
    )
);
