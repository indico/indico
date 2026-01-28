// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useSelector} from 'react-redux';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {FinalSubmitButton} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {PaperState} from '../models';
import {getCurrentUser, getPaperDetails} from '../selectors';

import RevisionSubmissionForm from './RevisionSubmissionForm';

export default function SubmitRevision() {
  const {
    state: {name: stateName},
    event: {id: eventId},
    contribution: {id: contributionId},
  } = useSelector(getPaperDetails);
  const currentUser = useSelector(getCurrentUser);

  if (stateName !== PaperState.to_be_corrected) {
    return null;
  }

  return (
    <div
      className="i-timeline-item"
      id="proposal-revision-submission-box"
      style={{position: 'relative', zIndex: -1}}
    >
      <UserAvatar user={currentUser} />
      <div className="i-timeline-item-box header-indicator-left">
        <div className="i-box-header flexrow">
          <Translate>Upload corrected revision</Translate>
        </div>
        <div className="i-box-content">
          <RevisionSubmissionForm eventId={eventId} contributionId={contributionId}>
            <FinalSubmitButton
              type="submit"
              label={Translate.string('Submit new revision')}
              style={{marginTop: 10}}
              primary
            />
          </RevisionSubmissionForm>
        </div>
      </div>
    </div>
  );
}
