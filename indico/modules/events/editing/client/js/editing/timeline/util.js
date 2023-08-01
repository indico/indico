// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';

import {RevisionType} from 'indico/modules/events/editing/models';
import {Translate} from 'indico/react/i18n';

import {filePropTypes} from './FileManager/util';

// This method defines each revision as a block
// with a label referring to its previous state transition
export function processRevisions(revisions) {
  console.log(revisions);
  return revisions.map((revision, i) => {
    const previousRevision = getPreviousRevisionWithFiles(revisions, i);
    // Set the state on the files that were added/modified in this revision
    let files = revision.files;
    if (previousRevision && files?.length) {
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
      header: getRevisionHeader(revisions, revision) || revision.header,
      items: _.sortBy(revision.comments, 'createdDt'),
      files,
    };
  });
}

function getPreviousRevisionWithFiles(revisions, index) {
  return revisions
    .slice(0, index)
    .reverse()
    .find(revision => !revision.isUndone && revision.files?.length);
}

function getRevisedRevision(revisions, revision) {
  return revisions
    .slice(0, revisions.indexOf(revision))
    .reverse()
    .find(r => !r.isUndone || revision.isUndone);
}

function getRevisionHeader(revisions, revision) {
  const revisedRevisionType = getRevisedRevision(revisions, revision)?.type.name;
  switch (revision.type.name) {
    case RevisionType.ready_for_review:
      if ([RevisionType.new, RevisionType.ready_for_review].includes(revisedRevisionType)) {
        return Translate.string('Revision has been replaced');
      }
      return null;
    case RevisionType.needs_submitter_confirmation:
      return Translate.string('{editorName} (editor) has made some changes to the paper', {
        editorName: revision.user.fullName,
      });
    case RevisionType.changes_acceptance:
      return Translate.string('Submitter has accepted proposed changes');
    case RevisionType.changes_rejection:
      return Translate.string('Submitter has rejected proposed changes');
    case RevisionType.needs_submitter_changes:
      return Translate.string('Submitter has been asked to make some changes');
    case RevisionType.acceptance:
      if (revisedRevisionType === RevisionType.needs_submitter_confirmation) {
        return Translate.string('{editorName} (editor) has accepted after making some changes', {
          editorName: revision.user.fullName,
        });
      }
      return Translate.string('{editorName} (editor) has accepted this revision', {
        editorName: revision.user.fullName,
      });
    case RevisionType.rejection:
      return Translate.string('{editorName} (editor) has rejected this revision', {
        editorName: revision.user.fullName,
      });
    default:
      return null;
  }
}

export const userPropTypes = {
  identifier: PropTypes.string.isRequired,
  fullName: PropTypes.string.isRequired,
  avatarURL: PropTypes.string.isRequired,
  id: PropTypes.number.isRequired,
};

const typePropTypes = {
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
  canModify: PropTypes.bool,
  user: PropTypes.shape(userPropTypes),
  header: PropTypes.string,
  text: PropTypes.string,
  html: PropTypes.string,
  internal: PropTypes.bool,
  system: PropTypes.bool,
  isUndone: PropTypes.bool,
  isEditor: PropTypes.bool,
  modifyCommentURL: PropTypes.string,
};

// Type that represents a revision block (with files)
export const blockPropTypes = {
  id: PropTypes.number.isRequired,
  user: PropTypes.shape(userPropTypes).isRequired,
  createdDt: PropTypes.string.isRequired,
  type: PropTypes.shape(typePropTypes).isRequired,
  isUndone: PropTypes.bool,
  isEditor: PropTypes.bool,
  comment: PropTypes.string.isRequired,
  commentHtml: PropTypes.string.isRequired,
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)).isRequired,
  items: PropTypes.arrayOf(PropTypes.shape(blockItemPropTypes)).isRequired,
  customActions: PropTypes.array.isRequired,
  customActionURL: PropTypes.string,
  downloadFilesURL: PropTypes.string,
};
