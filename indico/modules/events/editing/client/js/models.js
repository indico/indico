// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Translate} from 'indico/react/i18n';

export const RevisionType = {
  new: 'new',
  ready_for_review: 'ready_for_review',
  needs_submitter_confirmation: 'needs_submitter_confirmation',
  changes_acceptance: 'changes_acceptance',
  changes_rejection: 'changes_rejection',
  needs_submitter_changes: 'needs_submitter_changes',
  acceptance: 'acceptance',
  rejection: 'rejection',
  replacement: 'replacement',
};

export const RevisionTypeStates = {
  [RevisionType.new]: 'new',
  [RevisionType.ready_for_review]: 'ready_for_review',
  [RevisionType.needs_submitter_confirmation]: 'needs_submitter_confirmation',
  [RevisionType.changes_acceptance]: 'accepted',
  [RevisionType.changes_rejection]: 'needs_submitter_changes',
  [RevisionType.needs_submitter_changes]: 'needs_submitter_changes',
  [RevisionType.acceptance]: 'accepted',
  [RevisionType.rejection]: 'rejected',
  [RevisionType.replacement]: 'replaced',
};

export const EditingReviewAction = {
  accept: 'accept',
  reject: 'reject',
  update: 'update',
  update_accept: 'update_accept',
  requestUpdate: 'request_update',
};

export const EditableType = {
  paper: 'paper',
  slides: 'slides',
  poster: 'poster',
};

export const EditableTypeTitles = {
  paper: Translate.string('Paper'),
  slides: Translate.string('Slides'),
  poster: Translate.string('Poster'),
};

export const editableTypeOrder = ['paper', 'slides', 'poster'];

export const EditableStatus = {
  replaced: Translate.string('Replaced', 'Editable'),
  needs_submitter_confirmation: Translate.string('Needs submitter confirmation', 'Editable'),
  rejected: Translate.string('Rejected', 'Editable'),
  accepted_submitter: Translate.string('Accepted by submitter', 'Editable'),
  accepted: Translate.string('Accepted', 'Editable'),
  needs_submitter_changes: Translate.string('Needs submitter changes', 'Editable'),
  not_submitted: Translate.string('Not submitted', 'Editable'),
  ready_for_review: Translate.string('Ready for review', 'Editable'),
  new: Translate.string('New', 'Editable'),
};

export const EditableEditingTitles = {
  paper: Translate.string('Paper Editing'),
  slides: Translate.string('Slides Editing'),
  poster: Translate.string('Poster Editing'),
};

export const GetNextEditableTitles = {
  paper: Translate.string('Get next paper'),
  poster: Translate.string('Get next poster'),
  slides: Translate.string('Get next slides'),
};
