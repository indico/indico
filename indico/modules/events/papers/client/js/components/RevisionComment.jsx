// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Confirm, Popup} from 'semantic-ui-react';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {getChangedValues} from 'indico/react/forms';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import {deleteComment, updateComment as updateCommentAction} from '../actions';
import {CommentVisibility} from '../models';
import {getPaperContribution, getPaperEvent, isDeletingComment} from '../selectors';

import CommentForm from './CommentForm';

export default function RevisionComment({comment, revision}) {
  const dispatch = useDispatch();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const {id: eventId} = useSelector(getPaperEvent);
  const {id: contributionId} = useSelector(getPaperContribution);
  const isDeletingCommentInProgress = useSelector(isDeletingComment);

  const updateComment = async (formData, form) => {
    const rv = await dispatch(
      updateCommentAction(
        eventId,
        contributionId,
        revision.id,
        comment.id,
        getChangedValues(formData, form)
      )
    );
    if (rv.error) {
      return rv.error;
    }
  };

  return (
    <div className="i-timeline-item">
      <UserAvatar user={comment.user} />
      <div className="flexrow i-timeline-item-content">
        <div className="i-timeline-item-box header-indicator-left">
          <div className="i-box-header flexrow" style={{display: isEditing ? 'none' : 'flex'}}>
            <div className="f-self-stretch">
              <Translate>
                <Param name="userName" value={comment.user.fullName} wrapper={<strong />} /> left a
                comment
              </Translate>{' '}
              {comment.visibility.name !== CommentVisibility.contributors && (
                <Popup
                  trigger={
                    <i
                      className={`review-comment-visibility ${comment.visibility.name} icon-shield`}
                    />
                  }
                  content={comment.visibility.title}
                  position="bottom center"
                />
              )}{' '}
              <time
                dateTime={serializeDate(comment.createdDt, moment.HTML5_FMT.DATETIME_LOCAL_SECONDS)}
              >
                {serializeDate(comment.createdDt, 'LL')}
              </time>
              {comment.modifiedDt && (
                <Popup
                  trigger={
                    <span className="review-comment-edited">
                      {' '}
                      · <Translate>edited</Translate>
                    </span>
                  }
                  content={Translate.string('On {modificationDate} by {modifiedBy}', {
                    modificationDate: serializeDate(comment.modifiedDt, 'LL'),
                    modifiedBy: comment.modifiedBy.fullName,
                  })}
                  position="bottom center"
                />
              )}
            </div>
            {comment.canEdit && (
              <div className="review-comment-action hide-if-locked">
                <Popup
                  position="bottom center"
                  content={Translate.string('Edit comment')}
                  trigger={
                    <a className="i-link icon-edit" onClick={() => setIsEditing(!isEditing)} />
                  }
                />{' '}
                <Popup
                  position="bottom center"
                  content={Translate.string('Remove comment')}
                  trigger={<a onClick={() => setConfirmOpen(true)} className="i-link icon-cross" />}
                />
                <Confirm
                  size="tiny"
                  header={Translate.string('Remove comment')}
                  open={confirmOpen}
                  content={Translate.string('Are you sure you want to remove this comment?')}
                  onCancel={() => setConfirmOpen(false)}
                  closeOnDimmerClick={!isDeletingCommentInProgress}
                  closeOnEscape={!isDeletingCommentInProgress}
                  onConfirm={async () => {
                    const rv = await dispatch(
                      deleteComment(eventId, contributionId, revision.id, comment.id)
                    );
                    if (!rv.error) {
                      setConfirmOpen(false);
                    }
                  }}
                  cancelButton={
                    <Button
                      content={Translate.string('Cancel')}
                      disabled={isDeletingCommentInProgress}
                    />
                  }
                  confirmButton={
                    <Button
                      content={Translate.string('Remove comment')}
                      loading={isDeletingCommentInProgress}
                      disabled={isDeletingCommentInProgress}
                      negative
                    />
                  }
                  closeIcon={!isDeletingCommentInProgress}
                />
              </div>
            )}
          </div>
          <div className="i-box-content js-form-container">
            {isEditing ? (
              <CommentForm
                onSubmit={updateComment}
                onToggleExpand={visible => {
                  if (!visible) {
                    setIsEditing(false);
                  }
                }}
                comment={comment}
                expanded
              />
            ) : (
              <div className="markdown-text" dangerouslySetInnerHTML={{__html: comment.html}} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

RevisionComment.propTypes = {
  comment: PropTypes.object.isRequired,
  revision: PropTypes.object.isRequired,
};
