// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';

import {FinalRevisionState, InitialRevisionState} from 'indico/modules/events/editing/models';
import {Translate} from 'indico/react/i18n';

import {filePropTypes} from './FileManager/util';

// This method defines each revision as a block
// with a label referring to its previous state transition
export function processRevisions(revisions) {
  let revisionState;
  return revisions.map(revision => {
    const items = [...revision.comments];
    const header = revisionState;
    revisionState = getRevisionTransition(revision);
    // Generate the comment header
    if (revisionState) {
      const author = revision.editor || revision.submitter;
      items.push(commentFromState(revision, revisionState, author));
    }
    return {
      ...revision,
      // use the previous state transition as current block header
      header: header || revision.header,
      items,
    };
  });
}

export function commentFromState(revision, state, user) {
  const {finalState, id, createdDt, submitter} = revision;
  return {
    id: `custom-item-${id}-${createdDt}-${finalState.name}`,
    revisionId: id,
    header: state,
    createdDt,
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
    [FinalRevisionState.needs_submitter_changes]: Translate.string(
      'Submitter rejected proposed changes'
    ),
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

export function getRevisionTransition(revision) {
  const headerStates = revisionStates[revision.initialState.name] || revisionStates['any'];
  const header = headerStates[revision.finalState.name];
  return typeof header === 'function' ? header(revision) : header;
}

export const userPropTypes = {
  identifier: PropTypes.string.isRequired,
  fullName: PropTypes.string.isRequired,
  avatarBgColor: PropTypes.string.isRequired,
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
  createdDt: PropTypes.string.isRequired,
  modifiedDt: PropTypes.string,
  canModify: PropTypes.bool,
  user: PropTypes.shape(userPropTypes),
  header: PropTypes.string,
  text: PropTypes.string,
  html: PropTypes.string,
  internal: PropTypes.bool,
  system: PropTypes.bool,
  custom: PropTypes.bool,
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
