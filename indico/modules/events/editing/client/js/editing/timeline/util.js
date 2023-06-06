// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';

import {FinalRevisionState, InitialRevisionState} from 'indico/modules/events/editing/models';
import {Translate} from 'indico/react/i18n';

import {filePropTypes} from './FileManager/util';

export const isRequestChangesWithFiles = (revision, previousRevision) =>
  previousRevision &&
  revision.reviewedDt &&
  revision.editor &&
  previousRevision.editor &&
  previousRevision.finalState.name === FinalRevisionState.needs_submitter_changes &&
  revision.finalState.name === FinalRevisionState.needs_submitter_changes &&
  revision.reviewedDt === previousRevision.reviewedDt &&
  revision.editor.identifier === previousRevision.editor.identifier;

// This method defines each revision as a block
// with a label referring to its previous state transition
export function processRevisions(revisions) {
  let revisionState;
  return revisions.map((revision, i) => {
    const items = revision.comments.map(c =>
      c.undoneJudgment.name === FinalRevisionState.none
        ? c
        : {
            ...c,
            header: getRevisionTransition(
              {...revision, finalState: c.undoneJudgment},
              {isLatestRevision: true}
            ),
            createdDt: c.createdDt,
            custom: true,
          }
    );
    const header = revisionState;
    const isLatestRevision = i === revisions.length - 1;
    const previousRevision = getPreviousValidRevision(revisions, i);
    const nextRevision = getNextValidRevision(revisions, i);
    revisionState = getRevisionTransition(revision, {isLatestRevision});
    // Generate the comment header
    if (
      revisionState &&
      !isRequestChangesWithFiles(revision, previousRevision) &&
      !isEditorRevision(revision, nextRevision)
    ) {
      const author = revision.editor || revision.submitter;
      items.push(commentFromState(revision, revisionState, author));
    }
    // Set the state on the files that were added/modified in this revision
    let files = revision.files;
    if (previousRevision && previousRevision.files && files) {
      const previousFilesUUIDs = new Set(previousRevision.files.map(f => f.uuid));
      const previousFilenames = new Set(previousRevision.files.map(f => f.filename));
      files = files.map(f => {
        if (!previousFilesUUIDs.has(f.uuid)) {
          if (previousFilenames.has(f.filename)) {
            return {...f, state: 'modified'};
          }
          return {...f, state: 'added'};
        }
        return f;
      });
    }
    return {
      ...revision,
      // use the previous state transition as current block header, unless the revision has been undone
      header: revision.finalState.name !== FinalRevisionState.undone && (header || revision.header),
      revisionCommentHtml: isEditorRevision(previousRevision, revision)
        ? previousRevision.commentHtml
        : '',
      items: _.sortBy(items, 'createdDt'),
      files,
    };
  });
}

export function isEditorRevision(previousRevision, revision) {
  return (
    revision &&
    revision.finalState.name !== FinalRevisionState.undone &&
    previousRevision &&
    (revision.initialState.name === InitialRevisionState.needs_submitter_confirmation ||
      isRequestChangesWithFiles(revision, previousRevision)) &&
    previousRevision.editor &&
    previousRevision.editor.identifier === revision.submitter.identifier
  );
}

export function getPreviousValidRevision(revisions, index) {
  return revisions
    .slice(0, index)
    .reverse()
    .find(revision => revision.finalState.name !== FinalRevisionState.undone);
}

export function getNextValidRevision(revisions, index) {
  return revisions
    .slice(index + 1)
    .find(revision => revision.finalState.name !== FinalRevisionState.undone);
}

export function commentFromState(revision, state, user) {
  const {finalState, id, reviewedDt, submitter} = revision;
  return {
    id: `custom-item-${id}-${reviewedDt}-${finalState.name}`,
    revisionId: id,
    header: state,
    createdDt: reviewedDt,
    user: user || submitter,
    custom: true,
    html: revision.commentHtml,
  };
}

// The top-down order defines a description for each state transition in a revision
// [initialState, finalState] -> value | method -> value
export const revisionStates = {
  [InitialRevisionState.needs_submitter_confirmation]: {
    [FinalRevisionState.accepted]: revision => {
      return revision.editor !== null
        ? Translate.string('Editor has accepted after making some changes')
        : Translate.string('Submitter has accepted proposed changes');
    },
    [FinalRevisionState.needs_submitter_changes]: (__, {isLatestRevision}) => {
      return isLatestRevision
        ? Translate.string('Submitter rejected proposed changes')
        : Translate.string('Submitter rejected proposed changes and uploaded a new revision');
    },
  },
  any: {
    [FinalRevisionState.replaced]: Translate.string('Revision has been replaced'),
    [FinalRevisionState.accepted]: Translate.string('Revision has been accepted'),
    [FinalRevisionState.rejected]: Translate.string('Revision has been rejected'),
    [FinalRevisionState.needs_submitter_changes]: Translate.string(
      'Submitter has been asked to make some changes'
    ),
    [FinalRevisionState.needs_submitter_confirmation]: revision =>
      Translate.string('{editorName} (editor) has made some changes to the paper', {
        editorName: revision.editor?.fullName || '',
      }),
  },
};

export function getRevisionTransition(revision, revisionMetadata) {
  const headerStates = revisionStates[revision.initialState.name] || revisionStates['any'];
  const header = headerStates[revision.finalState.name];
  return typeof header === 'function' ? header(revision, revisionMetadata) : header;
}

export const userPropTypes = {
  identifier: PropTypes.string.isRequired,
  fullName: PropTypes.string.isRequired,
  avatarURL: PropTypes.string.isRequired,
  id: PropTypes.number.isRequired,
};

const statePropTypes = {
  cssClass: PropTypes.string,
  name: PropTypes.string.isRequired,
  title: PropTypes.string,
};

// Type that represents a revision comment block
// (a simplified-ish version of the revision blocks below)
export const blockItemPropTypes = {
  id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]).isRequired,
  revisionId: PropTypes.number.isRequired,
  createdDt: PropTypes.string,
  modifiedDt: PropTypes.string,
  reviewedDt: PropTypes.string,
  canModify: PropTypes.bool,
  user: PropTypes.shape(userPropTypes),
  header: PropTypes.string,
  text: PropTypes.string,
  html: PropTypes.string,
  internal: PropTypes.bool,
  system: PropTypes.bool,
  custom: PropTypes.bool,
  undoneJudgment: PropTypes.shape(statePropTypes),
  modifyCommentURL: PropTypes.string,
};

// Type that represents a revision block (with files)
export const blockPropTypes = {
  id: PropTypes.number.isRequired,
  submitter: PropTypes.shape(userPropTypes).isRequired,
  editor: PropTypes.shape(userPropTypes),
  createdDt: PropTypes.string.isRequired,
  initialState: PropTypes.shape(statePropTypes).isRequired,
  finalState: PropTypes.shape(statePropTypes).isRequired,
  comment: PropTypes.string.isRequired,
  commentHtml: PropTypes.string.isRequired,
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)).isRequired,
  items: PropTypes.arrayOf(PropTypes.shape(blockItemPropTypes)).isRequired,
  customActions: PropTypes.array.isRequired,
  customActionURL: PropTypes.string,
  downloadFilesURL: PropTypes.string,
};
