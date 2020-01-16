// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const FinalRevisionState = {
  none: 'none',
  replaced: 'replaced',
  needs_submitter_confirmation: 'needs_submitter_confirmation',
  needs_submitter_changes: 'needs_submitter_changes',
  accepted: 'accepted',
  rejected: 'rejected',
};

export const InitialRevisionState = {
  ready_for_review: 'ready_for_review',
  needs_submitter_confirmation: 'needs_submitter_confirmation',
};

export const EditingReviewAction = {
  accept: 'accept',
  reject: 'reject',
  update: 'update',
  requestUpdate: 'request_update',
};
