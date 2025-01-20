// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useDispatch, useSelector} from 'react-redux';

// import {
//   ContributionCreateForm,
//   ContributionEditForm,
// } from 'indico/modules/events/contributions/ContributionForm';

import * as actions from '../actions';
import * as selectors from '../selectors';

export default function ContributionEntryForm() {
  const dispatch = useDispatch();
  const {eventId} = useSelector(selectors.getStaticData);
  const entryType = useSelector(selectors.getModalType);
  const entry = useSelector(selectors.getModalEntry);
  const personLinkFieldParams = {}; // TODO

  const handleClose = () => dispatch(actions.closeModal());

  if (entryType !== 'contribution') {
    return null;
  }

  return entry ? (
    <ContributionEditForm
      eventId={eventId}
      contribId={entry.contributionId}
      personLinkFieldParams={personLinkFieldParams}
      onClose={handleClose}
    />
  ) : (
    <ContributionCreateForm
      eventId={eventId}
      personLinkFieldParams={personLinkFieldParams}
      onClose={handleClose}
    />
  );
}
