// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createSelector} from 'reselect';

import {Translate} from 'indico/react/i18n';
import {InitialRevisionState, FinalRevisionState} from './models';

function shouldCreateNewRevision({initialState, finalState}) {
  return (
    initialState.name === InitialRevisionState.ready_for_review &&
    ![
      FinalRevisionState.replaced,
      FinalRevisionState.accepted,
      FinalRevisionState.rejected,
    ].includes(finalState.name)
  );
}

function createNewCustomItemFromRevision(revision, updates) {
  return {
    id: `custom-item-${revision.id}-${revision.createdDt}-${updates.state}`,
    createdDt: revision.createdDt,
    user: revision.submitter,
    custom: true,
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

    if (revisions.length > 1 && shouldCreateNewRevision(revision)) {
      newRevisions.push({
        ..._.omit(currentRevision, 'comments'),
        number:
          finalState.name === FinalRevisionState.needs_submitter_confirmation
            ? numberOfRevisions
            : numberOfRevisions++,
        items,
      });

      if (index === revisions.length - 1) {
        currentRevision = {...revision};
      } else {
        currentRevision = {...revisions[index + 1]};
      }

      items = [...currentRevision.comments];
    }

    if (initialState.name === InitialRevisionState.needs_submitter_confirmation) {
      const previousRevision = revisions[index - 1];

      currentRevision.header = Translate.string('Editor requested some changes');
      currentRevision.comment = previousRevision.comment;
      currentRevision.commentHtml = previousRevision.commentHtml;
    }

    if (finalState.name === FinalRevisionState.replaced) {
      const updatedRevision = revisions[index + 1];

      items.push(
        createNewCustomItemFromRevision(updatedRevision, {
          header: Translate.string('Revision has been replaced'),
          state: FinalRevisionState.replaced,
        })
      );

      // Don't create a new top-level entry for the new (replaced) revision if it is the last one
      if (updatedRevision.finalState.name === FinalRevisionState.none) {
        break;
      }
    } else if (revision.finalState.name === FinalRevisionState.needs_submitter_changes) {
      items.push(
        createNewCustomItemFromRevision(revision, {
          user: revisions[0].submitter,
          header: Translate.string('Submitter rejected proposed changes'),
          state: 'rejected',
        })
      );
    } else if (revision.finalState.name === FinalRevisionState.accepted) {
      items.push(
        createNewCustomItemFromRevision(revision, {
          header: Translate.string('Revision has been accepted'),
          state: 'accepted',
          html: revision.commentHtml,
        })
      );
    } else if (revision.finalState.name === FinalRevisionState.rejected) {
      items.push(
        createNewCustomItemFromRevision(revision, {
          header: Translate.string('Revision has been rejected'),
          state: 'rejected',
          html: revision.commentHtml,
        })
      );
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
export const isLoading = state => state.timeline.isLoading;
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
    (lastRevision.finalState.name === 'none' ? lastRevision.initialState : lastRevision.finalState)
);
export const getStaticData = state => state.staticData;
