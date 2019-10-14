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
import {Button, Confirm, Header} from 'semantic-ui-react';

import {serializeDate} from 'indico/utils/date';
import {Param, Translate} from 'indico/react/i18n';

import {deleteComment} from '../actions';
import {getPaperContribution, getPaperEvent, getPaperPermissions} from '../selectors';
import UserAvatar from './UserAvatar';

export default function RevisionComment({comment, revision}) {
  const dispatch = useDispatch();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const {
    comments: {edit: editableComments},
  } = useSelector(getPaperPermissions);
  const {id: eventId} = useSelector(getPaperEvent);
  const {id: contributionId} = useSelector(getPaperContribution);

  return (
    <div id={`review-comment-${comment.id}`} className="i-timeline-item">
      <UserAvatar user={comment.user} />
      <div className="flexrow i-timeline-item-content">
        <div className="i-timeline-item-box header-indicator-left">
          <div className="i-box-header flexrow">
            <div className="f-self-stretch">
              <Translate>
                <Param name="userName" value={comment.user.fullName} wrapper={<strong />} /> left a
                comment
              </Translate>{' '}
              {comment.visibility !== 'contributors' && (
                <i
                  className={`review-comment-visibility ${comment.visibility.name} icon-shield`}
                  title={comment.visibility.title}
                />
              )}
              <time dateTime={serializeDate(comment.createdDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                {serializeDate(comment.createdDt, 'D MMM YYYY')}
              </time>
              {comment.modifiedDt && (
                <span
                  className="review-comment-edited"
                  title={Translate.string('On {modificationDate} by {modifiedBy}', {
                    modificationDate: serializeDate(comment.modifiedDt, 'D MMM YYYY'),
                    modifiedBy: comment.modifiedBy.fullName,
                  })}
                >
                  {' '}
                  · <Translate>edited</Translate>
                </span>
              )}
            </div>
            {editableComments.includes(comment.id) && (
              <div className="review-comment-action hide-if-locked">
                <a
                  href="#"
                  className="i-link icon-edit js-edit-comment"
                  title={Translate.string('Edit comment')}
                  data-form-container={`#review-comment-${comment.id} .js-form-container`}
                />{' '}
                <a
                  onClick={() => setConfirmOpen(true)}
                  className="i-link icon-cross js-delete-comment"
                  title={Translate.string('Remove comment')}
                />
                <Confirm
                  header={
                    <Header icon="warning sign" content={Translate.string('Remove comment')} />
                  }
                  open={confirmOpen}
                  content={Translate.string('Are you sure you want to remove this comment?')}
                  onCancel={() => setConfirmOpen(false)}
                  onConfirm={() => {
                    dispatch(deleteComment(eventId, contributionId, revision.id, comment.id));
                    setConfirmOpen(false);
                  }}
                  cancelButton={Translate.string('Cancel')}
                  confirmButton={<Button content={Translate.string('Remove comment')} negative />}
                  closeIcon
                />
              </div>
            )}
          </div>
          <div className="i-box-content js-form-container">
            <div className="markdown-text">{comment.text}</div>
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
