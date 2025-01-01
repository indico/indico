// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Confirm} from 'semantic-ui-react';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import {deleteRevisionComment, modifyRevisionComment} from './actions';
import CommentForm from './CommentForm';
import {getLastRevision} from './selectors';
import {blockItemPropTypes, INDICO_BOT_USER} from './util';

export default function Comment({
  revisionId,
  user,
  createdDt,
  modifiedDt,
  html,
  text,
  internal,
  system,
  canModify,
  modifyCommentURL,
}) {
  const [isDeletingComment, setIsDeletingComment] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [editCommentFormOpen, setEditCommentFormOpen] = useState(false);
  const lastRevision = useSelector(getLastRevision);
  const dispatch = useDispatch();
  const commentUser = system ? INDICO_BOT_USER : user;

  const modifyComment = async formData => {
    const rv = await dispatch(modifyRevisionComment(modifyCommentURL, formData));
    if (rv.error) {
      return rv.error;
    }
  };

  return (
    <div className="i-timeline-item">
      <UserAvatar user={commentUser} />
      <div className="flexrow i-timeline-item-content">
        <div className="i-timeline-item-box header-indicator-left">
          <div className="i-box-header flexrow">
            <div className="f-self-stretch">
              <Translate>
                <Param name="userName" value={commentUser.fullName} wrapper={<strong />} /> left a
                comment
              </Translate>{' '}
              {internal && (
                <i
                  className="review-comment-visibility internal icon-shield"
                  title={Translate.string('Visible only to editors')}
                />
              )}
              <time dateTime={serializeDate(createdDt, moment.HTML5_FMT.DATETIME_LOCAL_SECONDS)}>
                {serializeDate(createdDt, 'LLL')}
              </time>{' '}
              {modifiedDt && (
                <time
                  dateTime={serializeDate(modifiedDt, moment.HTML5_FMT.DATETIME_LOCAL_SECONDS)}
                  title={serializeDate(modifiedDt, 'LLL')}
                >
                  <span className="review-comment-edited">
                    <Translate>edited</Translate>
                  </span>
                </time>
              )}
            </div>
            {canModify && lastRevision.id === revisionId && (
              <div className="review-comment-action">
                <a
                  onClick={() => setEditCommentFormOpen(!editCommentFormOpen)}
                  className="i-link icon-edit"
                  title={Translate.string('Edit comment')}
                />{' '}
                <a
                  onClick={() => setConfirmOpen(true)}
                  className="i-link icon-cross"
                  title={Translate.string('Remove comment')}
                />
                <Confirm
                  size="tiny"
                  header={Translate.string('Remove comment')}
                  open={confirmOpen}
                  content={Translate.string('Are you sure you want to remove this comment?')}
                  closeOnDimmerClick={!isDeletingComment}
                  closeOnEscape={!isDeletingComment}
                  onCancel={() => setConfirmOpen(false)}
                  onConfirm={async () => {
                    setIsDeletingComment(true);

                    const rv = await dispatch(deleteRevisionComment(modifyCommentURL));
                    if (!rv.error) {
                      setConfirmOpen(false);
                    }

                    setIsDeletingComment(false);
                  }}
                  cancelButton={
                    <Button content={Translate.string('Cancel')} disabled={isDeletingComment} />
                  }
                  confirmButton={
                    <Button
                      content={Translate.string('Remove comment')}
                      loading={isDeletingComment}
                      disabled={isDeletingComment}
                      negative
                    />
                  }
                  closeIcon={!isDeletingComment}
                />
              </div>
            )}
          </div>
          <div className="i-box-content js-form-container">
            {editCommentFormOpen ? (
              <CommentForm
                onSubmit={modifyComment}
                onToggleExpand={setEditCommentFormOpen}
                initialValues={{text, internal}}
                expanded
              />
            ) : (
              <div className="markdown-text" dangerouslySetInnerHTML={{__html: html}} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

Comment.propTypes = blockItemPropTypes;
