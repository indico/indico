// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Confirm} from 'semantic-ui-react';

import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import {resetPaperJudgment} from '../actions';
import {getPaperDetails, getPaperPermissions, isPaperStateResetInProgress} from '../selectors';
import UserAvatar from './UserAvatar';

export default function RevisionJudgment({revision}) {
  const {state, judge, isLastRevision, judgmentCommentHtml, judgmentDt} = revision;
  const {event, contribution} = useSelector(getPaperDetails);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const {canJudge} = useSelector(getPaperPermissions);
  const isResetInProgress = useSelector(isPaperStateResetInProgress);
  const dispatch = useDispatch();

  if (state === 'submitted') {
    return null;
  }

  return (
    <div className="i-timeline-item">
      <UserAvatar user={judge} />
      <div className="i-timeline-item-box header-indicator-left">
        <div className="i-box-header flexrow">
          <div className="f-self-stretch">
            {state === 'accepted' && (
              <Translate>
                <Param name="judgeName" value={judge.fullName} wrapper={<strong />} /> accepted this
                paper.
              </Translate>
            )}
            {state === 'rejected' && (
              <Translate>
                <Param name="judgeName" value={judge.fullName} wrapper={<strong />} /> rejected this
                paper.
              </Translate>
            )}
            {state === 'to_be_corrected' && (
              <Translate>
                <Param name="judgeName" value={judge.fullName} wrapper={<strong />} /> asked for
                changes.
              </Translate>
            )}{' '}
            <time dateTime={serializeDate(judgmentDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
              {serializeDate(judgmentDt, 'LL')}
            </time>
          </div>
          {canJudge && isLastRevision && (
            <>
              <div className="hide-if-locked">
                <a
                  className="i-link icon-remove"
                  title={Translate.string('Reset judgment')}
                  onClick={() => setConfirmOpen(true)}
                />
              </div>
              <Confirm
                header={Translate.string('Confirm the operation')}
                open={confirmOpen}
                content={Translate.string(
                  'Do you really want to reset the judgment? This operation is irreversible.'
                )}
                onCancel={() => setConfirmOpen(false)}
                onConfirm={() => {
                  dispatch(resetPaperJudgment(event.id, contribution.id));
                }}
                cancelButton={
                  <Button content={Translate.string('Cancel')} disabled={isResetInProgress} />
                }
                confirmButton={
                  <Button
                    content={Translate.string('Reset judgment')}
                    disabled={isResetInProgress}
                    loading={isResetInProgress}
                    negative
                  />
                }
                closeIcon={!isResetInProgress}
              />
            </>
          )}
        </div>
        <div className="i-box-content">
          {state === 'accepted' && <Translate>The paper was accepted.</Translate>}
          {state === 'rejected' && <Translate>The paper was rejected.</Translate>}
          {state === 'to_be_corrected' && <Translate>The paper requires changes.</Translate>}
          {judgmentCommentHtml && (
            <>
              <div className="titled-rule">
                <Translate>Comment</Translate>
              </div>
              <div dangerouslySetInnerHTML={{__html: judgmentCommentHtml}} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

RevisionJudgment.propTypes = {
  revision: PropTypes.object.isRequired,
};
