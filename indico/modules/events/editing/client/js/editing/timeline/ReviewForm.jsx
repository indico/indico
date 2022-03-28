// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import submitRevisionURL from 'indico-url:event_editing.api_create_submitter_revision';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Dropdown} from 'semantic-ui-react';

import EditableSubmissionButton from 'indico/modules/events/editing/editing/EditableSubmissionButton';
import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import {EditingReviewAction} from '../../models';

import {createRevisionComment} from './actions';
import CommentForm from './CommentForm';
import JudgmentBox from './judgment/JudgmentBox';
import JudgmentDropdownItems from './judgment/JudgmentDropdownItems';
import {getLastRevision, canJudgeLastRevision, getDetails, getStaticData} from './selectors';
import {blockPropTypes} from './util';

import './ReviewForm.module.scss';

const judgmentOptions = [
  {
    value: EditingReviewAction.accept,
    text: Translate.string('Accept'),
    class: 'accepted',
  },
  {
    value: EditingReviewAction.reject,
    text: Translate.string('Reject'),
    class: 'rejected',
  },
  {
    value: EditingReviewAction.update,
    text: Translate.string('Make changes'),
    class: 'needs-submitter-confirmation',
  },
  {
    value: EditingReviewAction.requestUpdate,
    text: Translate.string('Request changes'),
    class: 'needs-submitter-changes',
  },
];

export default function ReviewForm({block}) {
  const dispatch = useDispatch();
  const lastRevision = useSelector(getLastRevision);
  const canJudge = useSelector(canJudgeLastRevision);
  const {canPerformSubmitterActions, contribution} = useSelector(getDetails);
  const {eventId, editableType, fileTypes} = useSelector(getStaticData);
  const currentUser = {
    fullName: Indico.User.fullName,
    avatarURL: Indico.User.avatarURL,
  };

  const [commentFormVisible, setCommentFormVisible] = useState(false);
  const [judgmentType, setJudgmentType] = useState(null);

  const createComment = async (formData, form) => {
    const rv = await dispatch(createRevisionComment(lastRevision.createCommentURL, formData));
    if (rv.error) {
      return rv.error;
    }
    setTimeout(() => form.reset(), 0);
  };

  const onSubmit = (type, formData) =>
    indicoAxios.post(
      submitRevisionURL({
        event_id: eventId,
        contrib_id: contribution.id,
        type,
        revision_id: lastRevision.id,
      }),
      formData
    );

  const judgmentForm = (
    <div className="flexrow" styleName="judgment-form">
      <CommentForm onSubmit={createComment} onToggleExpand={setCommentFormVisible} />
      {canPerformSubmitterActions && (
        <>
          <span className="comment-or-review">
            <Translate>or</Translate>
          </span>
          <EditableSubmissionButton
            eventId={eventId}
            contributionId={contribution.id}
            contributionCode={contribution.code}
            fileTypes={{[editableType]: fileTypes}}
            uploadableFiles={lastRevision.files}
            text={Translate.string('Submit files')}
            onSubmit={onSubmit}
          />
        </>
      )}
      {!commentFormVisible && canJudge && (
        <div className="review-trigger flexrow">
          <span className="comment-or-review">
            <Translate>or</Translate>
          </span>
          <Dropdown
            className="judgment-btn"
            text={Translate.string('Judge')}
            direction="left"
            button
            floating
          >
            <Dropdown.Menu>
              <JudgmentDropdownItems options={judgmentOptions} setJudgmentType={setJudgmentType} />
            </Dropdown.Menu>
          </Dropdown>
        </div>
      )}
    </div>
  );

  return (
    <div className="i-timeline-item review-timeline-input">
      <UserAvatar user={currentUser} />
      <div className="i-timeline-item-box footer-only header-indicator-left">
        <div className="i-box-footer" style={{overflow: 'visible'}}>
          {judgmentType ? (
            <JudgmentBox
              block={block}
              judgmentType={judgmentType}
              onClose={() => setJudgmentType(null)}
              options={judgmentOptions}
            />
          ) : (
            judgmentForm
          )}
        </div>
      </div>
    </div>
  );
}

ReviewForm.propTypes = {
  block: PropTypes.shape(blockPropTypes).isRequired,
};
