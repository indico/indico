// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useSelector} from 'react-redux';

import {Translate} from 'indico/react/i18n';

import {getCurrentUser, getPaperDetails} from '../selectors';
import UserAvatar from './UserAvatar';

export default function SubmitRevision() {
  const {state} = useSelector(getPaperDetails);
  const currentUser = useSelector(getCurrentUser);

  if (state !== 'to_be_corrected') {
    return null;
  }

  return (
    <div className="i-timeline-item" id="proposal-revision-submission-box">
      <UserAvatar user={currentUser} />
      <div className="i-timeline-item-box header-indicator-left">
        <div className="i-box-header flexrow">
          <Translate>Upload corrected revision</Translate>
        </div>
        <div className="i-box-content" />
      </div>
    </div>
  );
}
