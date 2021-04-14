// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createSelector} from 'reselect';

import {FinalRevisionState, InitialRevisionState} from '../../models';

export const getDetails = state => (state.timeline ? state.timeline.details : null);
export const getNewDetails = state => (state.timeline ? state.timeline.newDetails : null);
export const isInitialEditableDetailsLoading = state =>
  state.timeline.loading && !state.timeline.details;
export const isTimelineOutdated = createSelector(
  getDetails,
  getNewDetails,
  (details, newDetails) => newDetails !== null && !_.isEqual(details, newDetails)
);
export const getTimelineBlocks = state => state.timeline.timelineBlocks;
export const getLastTimelineBlock = createSelector(
  getTimelineBlocks,
  blocks => blocks && blocks[blocks.length - 1]
);
export const getLastRevision = createSelector(
  getDetails,
  details => details && details.revisions[details.revisions.length - 1]
);
export const needsSubmitterChanges = createSelector(
  getLastRevision,
  lastRevision =>
    lastRevision && lastRevision.finalState.name === FinalRevisionState.needs_submitter_changes
);
export const needsSubmitterConfirmation = createSelector(
  getLastRevision,
  lastRevision =>
    lastRevision.initialState.name === InitialRevisionState.needs_submitter_confirmation &&
    lastRevision.finalState.name === FinalRevisionState.none &&
    lastRevision.editor === null
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
  getLastTimelineBlock,
  (publishableFileTypes, block) => {
    const usedFileTypes = new Set(block.files.map(f => f.fileType));
    return publishableFileTypes.some(ft => usedFileTypes.has(ft.id));
  }
);

export const getLastRevertableRevisionId = createSelector(
  getDetails,
  details => {
    if (!details || !details.revisions.length) {
      return null;
    }
    const latestRevision = details.revisions[details.revisions.length - 1];
    const lastFinalRev = details.revisions
      .slice()
      .reverse()
      .find(r => r.finalState.name !== FinalRevisionState.none);

    if (!lastFinalRev) {
      return null;
    }
    if (lastFinalRev.id !== latestRevision.id) {
      if (
        lastFinalRev.finalState.name !== FinalRevisionState.needs_submitter_confirmation ||
        latestRevision.finalState.name !== FinalRevisionState.none ||
        latestRevision.initialState.name !== InitialRevisionState.needs_submitter_confirmation
      ) {
        return null;
      }
    }
    return lastFinalRev.id;
  }
);

export const canPerformSubmitterActions = createSelector(
  getDetails,
  details => details && details.canPerformSubmitterActions
);

export const canPerformEditorActions = createSelector(
  getDetails,
  details => details && details.canPerformEditorActions
);

export const editingEnabled = createSelector(
  getDetails,
  details => details && details.editingEnabled
);

export const canJudgeLastRevision = createSelector(
  getLastRevision,
  canPerformEditorActions,
  (lastRevision, allowed) =>
    lastRevision.finalState.name === FinalRevisionState.none &&
    lastRevision.initialState.name !== InitialRevisionState.needs_submitter_confirmation &&
    allowed
);
