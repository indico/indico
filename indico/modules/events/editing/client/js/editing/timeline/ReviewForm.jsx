// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import submitRevisionURL from 'indico-url:event_editing.api_create_submitter_revision';

import _ from 'lodash';
import React, {useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {useDispatch, useSelector} from 'react-redux';
import {Dropdown, Form} from 'semantic-ui-react';

import EditableSubmissionButton from 'indico/modules/events/editing/editing/EditableSubmissionButton';
import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {FinalSubmitButton} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import {EditingReviewAction} from '../../models';

import {createRevisionComment, reviewEditable} from './actions';
import CommentForm from './CommentForm';
import {getFilesFromRevision} from './FileManager/util';
import AcceptRejectForm from './judgment/AcceptRejectForm';
import JudgmentBox from './judgment/JudgmentBox';
import JudgmentDropdownItems from './judgment/JudgmentDropdownItems';
import RequestChangesForm from './judgment/RequestChangesForm';
import UpdateFilesForm from './judgment/UpdateFilesForm';
import {
  getLastRevision,
  canJudgeLastRevision,
  getDetails,
  getStaticData,
  canReviewLastRevision,
  getLastRevisionWithFiles,
} from './selectors';

import './ReviewForm.module.scss';

const judgmentOptions = [
  {
    value: EditingReviewAction.accept,
    text: Translate.string('Accept'),
    color: 'green',
    class: 'accepted',
  },
  {
    value: EditingReviewAction.reject,
    text: Translate.string('Reject'),
    color: 'black',
    class: 'rejected',
  },
  {
    value: EditingReviewAction.update,
    text: Translate.string('Request approval'),
    color: 'yellow',
    class: 'needs-submitter-confirmation',
  },
  {
    value: EditingReviewAction.requestUpdate,
    text: Translate.string('Request changes'),
    color: 'red',
    class: 'needs-submitter-changes',
  },
];

export default function ReviewForm() {
  const dispatch = useDispatch();
  const lastRevision = useSelector(getLastRevision);
  const lastRevisionWithFiles = useSelector(getLastRevisionWithFiles);
  const canJudge = useSelector(canJudgeLastRevision);
  const canReview = useSelector(canReviewLastRevision);
  const {canPerformSubmitterActions, contribution, editor} = useSelector(getDetails);
  const {eventId, editableType, fileTypes} = useSelector(getStaticData);
  const currentUser = {
    fullName: Indico.User.fullName,
    avatarURL: Indico.User.avatarURL,
  };

  const [commentFormVisible, setCommentFormVisible] = useState(false);
  const [judgmentType, setJudgmentType] = useState(null);
  const [loading, setLoading] = useState(false);
  const files = getFilesFromRevision(fileTypes, lastRevisionWithFiles);

  const createComment = async (formData, form) => {
    const rv = await dispatch(createRevisionComment(lastRevision.createCommentURL, formData));
    if (rv.error) {
      return rv.error;
    }
    setTimeout(() => form.reset(), 0);
  };

  const handleSubmission = (type, formData) =>
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
    <div className="flexrow f-a-center" styleName="judgment-form">
      <CommentForm onSubmit={createComment} onToggleExpand={setCommentFormVisible} />
      {canPerformSubmitterActions && canReview && !editor && (
        <>
          <span className="comment-or-review">
            <Translate>or</Translate>
          </span>
          <EditableSubmissionButton
            eventId={eventId}
            contributionId={contribution.id}
            contributionCode={contribution.code}
            fileTypes={{[editableType]: fileTypes}}
            uploadableFiles={lastRevisionWithFiles.files}
            text={Translate.string('Submit files')}
            onSubmit={handleSubmission}
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

  const handleReview = async formData => {
    setLoading(true);
    const rv = await dispatch(reviewEditable(lastRevision, {...formData, action: judgmentType}));
    setLoading(false);
    if (rv.error) {
      return rv.error;
    }
    setJudgmentType(null); // TODO check if necessary
  };

  return (
    <div className="i-timeline-item review-timeline-input">
      <UserAvatar user={currentUser} />
      <div className="i-timeline-item-box footer-only header-indicator-left">
        <div className="i-box-footer" style={{overflow: 'visible'}}>
          {judgmentType ? (
            <JudgmentBox
              judgmentType={judgmentType}
              setJudgmentType={setJudgmentType}
              options={judgmentOptions}
              loading={loading}
            />
          ) : (
            judgmentForm
          )}
          <FinalForm
            initialValues={{
              comment: '',
              tags: lastRevision.tags
                .filter(t => !t.system)
                .map(t => t.id)
                .sort(),
              files,
            }}
            initialValuesEqual={_.isEqual}
            subscription={{}}
            onSubmit={handleReview}
          >
            {({handleSubmit}) => (
              <>
                <Form id="judgment-form" onSubmit={handleSubmit}>
                  {[EditingReviewAction.accept, EditingReviewAction.reject].includes(
                    judgmentType
                  ) && <AcceptRejectForm action={judgmentType} />}
                  {judgmentType === EditingReviewAction.update && <UpdateFilesForm />}
                  {judgmentType === EditingReviewAction.requestUpdate && <RequestChangesForm />}
                </Form>
                {judgmentType && (
                  <div styleName="judgment-submit-button">
                    <FinalSubmitButton
                      form="judgment-form"
                      label={Translate.string('Confirm')}
                      disabledUntilChange={judgmentType !== EditingReviewAction.accept}
                    />
                  </div>
                )}
              </>
            )}
          </FinalForm>
        </div>
      </div>
    </div>
  );
}
