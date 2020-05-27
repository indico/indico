// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createSelector} from 'reselect';

import {Translate} from 'indico/react/i18n';
import {InitialRevisionState, FinalRevisionState} from '../../models';

function shouldCreateNewRevision({initialState, finalState}) {
  return (
    initialState.name === InitialRevisionState.needs_submitter_confirmation ||
    (initialState.name === InitialRevisionState.ready_for_review &&
      ![
        FinalRevisionState.accepted,
        FinalRevisionState.rejected,
        FinalRevisionState.replaced,
      ].includes(finalState.name))
  );
}

function createNewCustomItemFromRevision(revision, updates) {
  return {
    id: `custom-item-${revision.id}-${revision.createdDt}-${updates.state}`,
    createdDt: revision.createdDt,
    user: revision.submitter,
    custom: true,
    revisionId: revision.id,
    ...updates,
  };
}

export function processRevisions(revisions) {
  const newRevisions = [];
  let numberOfRevisions = 1;
  let currentRevision = revisions[0];
  let items = [...currentRevision.comments];

  for (const [index, revision] of revisions.entries()) {
    const {initialState, finalState} = revision;

    if (!currentRevision) {
      currentRevision = {...revision};
      items = [...currentRevision.comments];
    }

    if (initialState.name === InitialRevisionState.needs_submitter_confirmation) {
      currentRevision.header = Translate.string('Editor has made some changes to the paper');
    }

    if (finalState.name === FinalRevisionState.replaced) {
      const updatedRevision = revisions[index + 1];

      items.push(
        createNewCustomItemFromRevision(updatedRevision, {
          header: Translate.string('Revision has been replaced'),
          state: FinalRevisionState.replaced,
        })
      );

      items = [...items, ...updatedRevision.comments];
    } else if (finalState.name === FinalRevisionState.accepted) {
      let header;
      if (
        revision.editor !== null &&
        initialState.name === InitialRevisionState.needs_submitter_confirmation
      ) {
        header = Translate.string('Editor has accepted after making some changes');
      } else if (initialState.name === InitialRevisionState.needs_submitter_confirmation) {
        header = Translate.string('Submitter has accepted proposed changes');
      } else {
        header = Translate.string('Revision has been accepted');
      }

      items.push(
        createNewCustomItemFromRevision(revision, {
          state: 'accepted',
          html: revision.commentHtml,
          header,
        })
      );
    } else if (finalState.name === FinalRevisionState.rejected) {
      items.push(
        createNewCustomItemFromRevision(revision, {
          header: Translate.string('Revision has been rejected'),
          state: 'rejected',
          html: revision.commentHtml,
        })
      );
    } else if (finalState.name === FinalRevisionState.needs_submitter_changes) {
      let header;
      if (initialState.name === InitialRevisionState.needs_submitter_confirmation) {
        header = Translate.string('Submitter rejected proposed changes');
      } else {
        header = Translate.string('Submitter has been asked to make some changes');
      }

      items.push(
        createNewCustomItemFromRevision(revision, {
          user: revisions[0].submitter,
          state: 'needs_submitter_changes',
          html: revision.commentHtml,
          header,
        })
      );
    } else if (finalState.name === FinalRevisionState.needs_submitter_confirmation) {
      items.push(
        createNewCustomItemFromRevision(revision, {
          user: revisions[0].submitter,
          header: Translate.string('Editor made some changes'),
          state: 'needs_submitter_confirmation',
          html: revision.commentHtml,
        })
      );
    }

    if (shouldCreateNewRevision(revision)) {
      newRevisions.push({
        ..._.omit(currentRevision, 'comments'),
        number: numberOfRevisions++,
        items,
      });

      currentRevision = null;
      items = [];
    }
  }

  if (currentRevision) {
    newRevisions.push({
      ..._.omit(currentRevision, 'comments'),
      number: numberOfRevisions++,
      items,
    });
  }

  return newRevisions;
}

export const getDetails = state => state.timeline.details;
export const isInitialEditableDetailsLoading = state =>
  state.timeline.loading && !state.timeline.details;
export const getTimelineBlocks = state => state.timeline.timelineBlocks;
export const getLastTimelineBlock = createSelector(
  getTimelineBlocks,
  blocks => blocks && blocks[blocks.length - 1]
);
export const getLastRevision = createSelector(
  getDetails,
  details => details && details.revisions[details.revisions.length - 1]
);
export const getLastState = createSelector(
  getLastRevision,
  lastRevision =>
    lastRevision &&
    (lastRevision.finalState.name === FinalRevisionState.none
      ? lastRevision.initialState
      : lastRevision.finalState)
);
export const hasLastState = createSelector(
  getLastRevision,
  lastRevision => lastRevision && lastRevision.finalState.name !== FinalRevisionState.none
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

export const getFileTypes = createSelector(
  getStaticData,
  staticData => {
    return staticData.fileTypes.map(fileType => {
      if (!fileType.filenameTemplate) {
        return fileType;
      }
      return {
        ...fileType,
        filenameTemplate: fileType.filenameTemplate.replace('{code}', staticData.contributionCode),
      };
    });
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
