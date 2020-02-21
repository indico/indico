// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useCallback} from 'react';
import {useDispatch, useSelector} from 'react-redux';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';

import CommentForm from './CommentForm';
import {addComment} from '../actions';
import {canCommentPaper, getPaperDetails, getCurrentUser} from '../selectors';

import './PaperReviewForm.module.scss';

export default function PaperReviewForm() {
  const {
    event: {id: eventId},
    contribution: {id: contributionId},
  } = useSelector(getPaperDetails);
  const user = useSelector(getCurrentUser);
  const canComment = useSelector(canCommentPaper);
  const dispatch = useDispatch();

  const createComment = useCallback(
    async formData => {
      const rv = await dispatch(addComment(eventId, contributionId, formData));
      if (rv.error) {
        return rv.error;
      }
    },
    [dispatch, eventId, contributionId]
  );

  return (
    <div className="i-timeline-item" styleName="review-timeline-input">
      <UserAvatar user={user} />
      <div className="i-timeline-item-box footer-only header-indicator-left">
        <div className="i-box-footer" style={{overflow: 'visible'}}>
          {canComment && <CommentForm onSubmit={createComment} />}
        </div>
      </div>
    </div>
  );
}
