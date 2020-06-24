// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Confirm, Icon, Popup} from 'semantic-ui-react';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import {resetPaperJudgment} from '../actions';
import {getPaperDetails, isPaperStateResetInProgress} from '../selectors';
import {PaperState} from '../models';

export default function RevisionJudgment({revision}) {
  const {state, judge, isLastRevision, judgmentCommentHtml, judgmentDt} = revision;
  const {event, contribution, canJudge} = useSelector(getPaperDetails);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const isResetInProgress = useSelector(isPaperStateResetInProgress);
  const dispatch = useDispatch();

  if (state === PaperState.submitted) {
    return null;
  }

  return (
    <div className="i-timeline-item">
      <UserAvatar user={judge} />
      <div className="i-timeline-item-box header-indicator-left">
        <div className="i-box-header flexrow">
          <div className="f-self-stretch">
            {state === PaperState.accepted && (
              <Translate>
                <Param name="judgeName" value={judge.fullName} wrapper={<strong />} /> accepted this
                paper.
              </Translate>
            )}
            {state === PaperState.rejected && (
              <Translate>
                <Param name="judgeName" value={judge.fullName} wrapper={<strong />} /> rejected this
                paper.
              </Translate>
            )}
            {state === PaperState.to_be_corrected && (
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
              <div>
                <Popup
                  position="bottom center"
                  content={Translate.string('Reset judgment')}
                  trigger={
                    <Icon link className="undo" color="grey" onClick={() => setConfirmOpen(true)} />
                  }
                />
              </div>
              <Confirm
                size="tiny"
                header={Translate.string('Confirm the operation')}
                open={confirmOpen}
                closeOnDimmerClick={!isResetInProgress}
                closeOnEscape={!isResetInProgress}
                content={Translate.string(
                  'Do you really want to reset the judgment? This operation is irreversible.'
                )}
                onCancel={() => setConfirmOpen(false)}
                onConfirm={async () => {
                  const rv = await dispatch(resetPaperJudgment(event.id, contribution.id));
                  if (!rv.error) {
                    setConfirmOpen(false);
                  }
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
          {state === PaperState.accepted && <Translate>The paper was accepted.</Translate>}
          {state === PaperState.rejected && <Translate>The paper was rejected.</Translate>}
          {state === PaperState.to_be_corrected && (
            <Translate>The paper requires changes.</Translate>
          )}
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
