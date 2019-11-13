// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';

import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import UserAvatar from './UserAvatar';

function Comment({comment}) {
  return (
    <div className="i-timeline-item">
      <UserAvatar user={comment.user} />
      <div className="flexrow i-timeline-item-content">
        <div className="i-timeline-item-box header-indicator-left">
          <div className="i-box-header flexrow">
            <div className="f-self-stretch">
              <Translate>
                <Param name="userName" value={comment.user.fullName} wrapper={<strong />} /> left a
                comment
              </Translate>{' '}
              <time dateTime={serializeDate(comment.createdDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                {serializeDate(comment.createdDt, 'LL')}
              </time>
              {comment.modifiedDt && (
                <span
                  className="review-comment-edited"
                  title={Translate.string('On {modificationDate}', {
                    modificationDate: serializeDate(comment.modifiedDt, 'LL'),
                  })}
                >
                  {' '}
                  · <Translate>edited</Translate>
                </span>
              )}
            </div>
          </div>
          <div className="i-box-content js-form-container">
            <div className="markdown-text" dangerouslySetInnerHTML={{__html: comment.html}} />
          </div>
        </div>
      </div>
    </div>
  );
}

const baseCommentProps = {
  createdDt: PropTypes.string.isRequired,
  html: PropTypes.string.isRequired,
  user: PropTypes.shape({
    fullName: PropTypes.string.isRequired,
    avatarBgColor: PropTypes.string.isRequired,
  }).isRequired,
};

const CommentPropType = PropTypes.shape({
  ...baseCommentProps,
  modifiedDt: PropTypes.string,
});

const CommentPropTypes = {
  comment: CommentPropType.isRequired,
};

Comment.propTypes = CommentPropTypes;

function CustomComment({comment}) {
  return (
    <div className="i-timeline-item">
      <UserAvatar user={comment.user} />
      <div className="flexrow i-timeline-item-content">
        <div className="i-timeline-item-box header-indicator-left">
          <div className={`${comment.html ? 'i-box-header' : ''} flexrow`}>
            <div className="f-self-stretch">
              {comment.header}{' '}
              <time dateTime={serializeDate(comment.createdDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
                {serializeDate(comment.createdDt, 'LL')}
              </time>
            </div>
          </div>
          {comment.html && (
            <div className="i-box-content js-form-container">
              <div className="markdown-text" dangerouslySetInnerHTML={{__html: comment.html}} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const CustomCommentPropType = PropTypes.shape({
  ...baseCommentProps,
  header: PropTypes.string.isRequired,
});

CustomComment.propTypes = {
  comment: CustomCommentPropType.isRequired,
};

export default function RevisionComments({comments, children}) {
  return (
    <div className="i-timeline">
      <div className="i-timeline with-line">
        <div className="i-timeline-connect-up" />
        {comments.map(comment => {
          const CommentComponent = comment.custom ? CustomComment : Comment;
          return <CommentComponent key={comment.id} comment={comment} />;
        })}
      </div>
      {children}
    </div>
  );
}

RevisionComments.propTypes = {
  comments: PropTypes.arrayOf(PropTypes.oneOfType([CommentPropType, CustomCommentPropType]))
    .isRequired,
  children: PropTypes.node,
};

RevisionComments.defaultProps = {
  children: null,
};
