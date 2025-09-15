// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import submitRevisionURL from 'indico-url:event_editing.api_create_submitter_revision';

import _ from 'lodash';
import React, {useState} from 'react';
import {Field, Form as FinalForm} from 'react-final-form';
import {useDispatch, useSelector} from 'react-redux';
import {Dropdown, Form, Popup} from 'semantic-ui-react';

import EditableSubmissionButton from 'indico/modules/events/editing/editing/EditableSubmissionButton';
import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {FinalCheckbox, FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {DirtyInitialValue} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import {EditingReviewAction} from '../../models';

import {createRevisionComment, reviewEditable, setDraftComment} from './actions';
import CommentForm from './CommentForm';
import {getFilesFromRevision} from './FileManager/util';
import JudgmentBoxHeader from './judgment/JudgmentBoxHeader';
import JudgmentDropdownItems from './judgment/JudgmentDropdownItems';
import FinalTagInput from './judgment/TagInput';
import UpdateFilesBox from './judgment/UpdateFilesBox';
import * as selectors from './selectors';

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
  const lastRevision = useSelector(selectors.getLastRevision);
  const lastRevisionWithFiles = useSelector(selectors.getLastRevisionWithFiles);
  const canJudge = useSelector(selectors.canJudgeLastRevision);
  const canReview = useSelector(selectors.canReviewLastRevision);
  const {canPerformSubmitterActions, contribution, editor} = useSelector(selectors.getDetails);
  const {eventId, editableType, fileTypes} = useSelector(selectors.getStaticData);
  const tagOptions = useSelector(selectors.getNonSystemTags);
  const isOutdated = useSelector(selectors.isTimelineOutdated);
  const draftComment = useSelector(selectors.getDraftComment);
  const currentUser = {
    fullName: Indico.User.fullName,
    avatarURL: Indico.User.avatarURL,
  };

  const [judgmentType, setJudgmentType] = useState(null);
  const [loading, setLoading] = useState(false);
  const [syncComment, setSyncComment] = useState(false);
  const files = getFilesFromRevision(fileTypes, lastRevisionWithFiles);

  const onCommentChange = value => {
    dispatch(setDraftComment(value));
  };

  const createComment = async (formData, form) => {
    const rv = await dispatch(createRevisionComment(lastRevision.createCommentURL, formData));
    if (rv.error) {
      return rv.error;
    }
    onCommentChange('');
    setTimeout(() => {
      form.reset();
      setSyncComment(true);
    }, 0);
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
      <CommentForm
        onSubmit={createComment}
        syncComment={syncComment}
        setSyncComment={setSyncComment}
        disabled={isOutdated}
        expanded={isOutdated}
      />
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
      {canJudge && (
        <div className="flexcol align-strech">
          <div className="review-trigger flexrow">
            <span className="comment-or-review">
              <Translate>or</Translate>
            </span>
            <Dropdown
              className="judgment-btn"
              text={Translate.string('Judge', 'Judge editable (verb)')}
              direction="left"
              disabled={isOutdated}
              button
              floating
            >
              <Dropdown.Menu>
                <JudgmentDropdownItems
                  options={judgmentOptions}
                  setJudgmentType={type => {
                    setSyncComment(true);
                    setJudgmentType(type);
                  }}
                />
              </Dropdown.Menu>
            </Dropdown>
          </div>
        </div>
      )}
    </div>
  );

  const handleReview = async formData => {
    setLoading(true);
    const data = _.omit(formData, [
      'upload_changes',
      ...(judgmentType === EditingReviewAction.reject ||
      ([EditingReviewAction.accept, EditingReviewAction.requestUpdate].includes(judgmentType) &&
        !formData.upload_changes)
        ? ['files']
        : []),
    ]);
    const rv = await dispatch(reviewEditable(lastRevision, {...data, action: judgmentType}));
    setLoading(false);
    if (rv.error) {
      return rv.error;
    }
    setJudgmentType(null);
  };

  return (
    <div className="i-timeline-item review-timeline-input">
      <UserAvatar user={currentUser} />
      <div className="i-timeline-item-box footer-only header-indicator-left">
        <div className="i-box-footer" style={{overflow: 'visible'}}>
          {!judgmentType && judgmentForm}
          <FinalForm
            initialValues={{
              comment: '',
              tags: lastRevision.tags
                .filter(t => !t.system)
                .map(t => t.id)
                .sort(),
              files,
              upload_changes: false,
            }}
            initialValuesEqual={_.isEqual}
            subscription={{}}
            onSubmit={handleReview}
          >
            {({handleSubmit}) =>
              judgmentType && (
                <Form id="judgment-form" onSubmit={handleSubmit}>
                  <JudgmentBoxHeader
                    judgmentType={judgmentType}
                    setJudgmentType={type => {
                      setSyncComment(true);
                      setJudgmentType(type);
                    }}
                    options={judgmentOptions}
                    loading={loading}
                  />
                  <FinalTextArea
                    name="comment"
                    placeholder={Translate.string('Leave a comment...')}
                    hideValidationError
                    autoFocus
                    required={judgmentType !== EditingReviewAction.accept}
                    onChange={onCommentChange}
                    /* otherwise changing required doesn't work properly if the field has been touched */
                    key={judgmentType}
                  />
                  {syncComment && (
                    <DirtyInitialValue
                      field="comment"
                      value={draftComment}
                      onUpdate={() => setSyncComment(false)}
                    />
                  )}
                  {[EditingReviewAction.accept, EditingReviewAction.requestUpdate].includes(
                    judgmentType
                  ) && (
                    <FinalCheckbox
                      name="upload_changes"
                      label={Translate.string('Upload files')}
                      showAsToggle
                    />
                  )}
                  <Field name="upload_changes" subscription={{value: true}}>
                    {({input: {value: uploadChanges}}) => (
                      <UpdateFilesBox
                        visible={
                          judgmentType === EditingReviewAction.update ||
                          ([EditingReviewAction.accept, EditingReviewAction.requestUpdate].includes(
                            judgmentType
                          ) &&
                            uploadChanges)
                        }
                        mustChange={judgmentType === EditingReviewAction.update || uploadChanges}
                        requirePublishable={[
                          EditingReviewAction.accept,
                          EditingReviewAction.update,
                        ].includes(judgmentType)}
                      />
                    )}
                  </Field>
                  <FinalTagInput name="tags" options={tagOptions} />
                  <div styleName="judgment-submit-button">
                    <Popup
                      trigger={
                        <div>
                          <FinalSubmitButton
                            label={Translate.string('Judge', 'Judge editable (verb)')}
                            disabledUntilChange={judgmentType !== EditingReviewAction.accept}
                            disabled={isOutdated}
                          />
                        </div>
                      }
                      content={Translate.string(
                        'This timeline is outdated. Please refresh the page.'
                      )}
                      disabled={!isOutdated}
                      // XXX: For some reason the button does not properly update with the correct
                      // `dirty` state after setting the `comment` value programmatically, but by
                      // also subscribing to `touched` we avoid this bug.
                      // If someone ever needs to change something there or test this behavior, it
                      // happens when you write a comment, then switch to judgment mode, then close
                      // the judgment form again and then switch to judgment mode again.
                      extraSubscription={{touched: true}}
                    />
                  </div>
                </Form>
              )
            }
          </FinalForm>
        </div>
      </div>
    </div>
  );
}
