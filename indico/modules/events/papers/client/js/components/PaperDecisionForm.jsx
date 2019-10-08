// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useCallback} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Form as FinalForm} from 'react-final-form';
import {Form} from 'semantic-ui-react';

import {FinalDropdown, FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {judgePaper} from '../actions';
import {
  canJudgePaper,
  getCurrentUser,
  getPaperDetails,
  isJudgingInProgress,
  isEventLocked,
} from '../selectors';
import UserAvatar from './UserAvatar';

import './PaperDecisionForm.module.scss';

const actionOptions = [
  {
    value: 'accept',
    text: Translate.string('Accept'),
  },
  {
    value: 'reject',
    text: Translate.string('Reject'),
  },
  {
    value: 'to_be_corrected',
    text: Translate.string('To be corrected'),
  },
];

export default function PaperDecisionForm() {
  const dispatch = useDispatch();
  const {
    event: {id: eventId},
    contribution: {id: contributionId},
  } = useSelector(getPaperDetails);
  const isLocked = useSelector(isEventLocked);
  const currentUser = useSelector(getCurrentUser);
  const isJudging = useSelector(isJudgingInProgress);
  const canJudge = useSelector(canJudgePaper);

  const submitPaperJudgment = useCallback(
    formData => {
      dispatch(judgePaper(eventId, contributionId, formData));
    },
    [dispatch, eventId, contributionId]
  );

  if (isLocked || !canJudge) {
    return null;
  }

  return (
    <div
      id="proposal-decision-box"
      className="i-timeline i-timeline-item"
      styleName="paper-decision-box"
    >
      <UserAvatar user={currentUser} />
      <div className="i-timeline-item-box footer-only header-indicator-left review-form">
        <div className="i-box-footer">
          <FinalForm onSubmit={submitPaperJudgment} initialValues={{action: 'accept', comment: ''}}>
            {fprops => (
              <Form id="judgment-form" onSubmit={fprops.handleSubmit} loading={isJudging}>
                <FinalDropdown name="action" options={actionOptions} selection required />
                <FinalTextArea
                  name="comment"
                  placeholder={Translate.string('Leave a comment for the submitter...')}
                />
                <FinalSubmitButton
                  label={Translate.string('Judge')}
                  form="judgment-form"
                  disabledUntilChange={false}
                />
              </Form>
            )}
          </FinalForm>
        </div>
      </div>
    </div>
  );
}
