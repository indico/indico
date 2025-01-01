// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useCallback, useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Dropdown, Icon} from 'semantic-ui-react';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {unsortedArraysEqual} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {createComment as createCommentAction, createReview, updateReview} from '../actions';
import {canCommentPaper, canReviewPaper, getPaperDetails, getCurrentUser} from '../selectors';

import CommentForm from './CommentForm';
import GroupReviewForm from './GroupReviewForm';

import './PaperReviewForm.module.scss';

export default function PaperReviewForm() {
  const {
    event: {id: eventId},
    contribution: {id: contributionId},
    lastRevision,
    isInFinalState,
  } = useSelector(getPaperDetails);
  const {reviewerData} = lastRevision;
  const [commentFormExpanded, setCommentFormExpanded] = useState(false);
  const [reviewGroup, setReviewGroup] = useState(null);
  const user = useSelector(getCurrentUser);
  const canComment = useSelector(canCommentPaper);
  const canReview = useSelector(canReviewPaper);
  const dispatch = useDispatch();

  const reviewGroups = reviewerData.groups.map(group => group.name);
  const reviewedGroups = reviewerData.reviewedGroups.map(group => group.name);

  const createComment = useCallback(
    async formData => {
      const rv = await dispatch(createCommentAction(eventId, contributionId, formData));
      if (rv.error) {
        return rv.error;
      }
    },
    [dispatch, eventId, contributionId]
  );

  const renderReviewTrigger = () => {
    return (
      <div className="review-trigger flexrow">
        <span className="comment-or-review">
          <Translate>or</Translate>
        </span>
        {reviewGroups.length === 1 ? (
          <Button onClick={() => setReviewGroup(reviewGroups[0])}>
            {reviewGroups[0] in reviewerData.reviews ? (
              <Translate>Change review</Translate>
            ) : (
              <Translate>Review</Translate>
            )}
          </Button>
        ) : (
          <Dropdown
            text={
              unsortedArraysEqual(reviewGroups, reviewedGroups)
                ? Translate.string('Change reviews')
                : Translate.string('Review', 'Review papers (verb)')
            }
            button
          >
            <Dropdown.Menu>
              {reviewerData.groups.map(group => (
                <Dropdown.Item key={group.name} onClick={() => setReviewGroup(group.name)}>
                  <span>{group.title}</span>
                  {group.name in reviewerData.reviews && <Icon name="checkmark" floated="right" />}
                </Dropdown.Item>
              ))}
            </Dropdown.Menu>
          </Dropdown>
        )}
      </div>
    );
  };

  const renderForm = () => {
    if (reviewGroup) {
      const group = reviewerData.groups.find(item => item.name === reviewGroup);
      const review = reviewerData.reviews[reviewGroup] || null;

      return (
        <GroupReviewForm
          review={review}
          group={group}
          onCancel={() => setReviewGroup(null)}
          onSubmit={async formData => {
            const action = review
              ? updateReview(eventId, contributionId, lastRevision.id, review.id, formData)
              : createReview(eventId, contributionId, group.name, formData);

            const rv = await dispatch(action);
            if (rv.error) {
              return rv.error;
            }
            setReviewGroup(null);
          }}
        />
      );
    } else if (canComment) {
      return (
        <div className="flexrow">
          <CommentForm onSubmit={createComment} onToggleExpand={setCommentFormExpanded} />
          {/*
            Show the "Review" button only if
            1. CommentForm is not focused
            2. There is at least one review type
            3. The paper is not in the final state
            4. The current user can review the paper
          */}
          {!commentFormExpanded &&
            reviewGroups.length > 0 &&
            !isInFinalState &&
            canReview &&
            renderReviewTrigger()}
        </div>
      );
    }
  };

  return (
    <div className="i-timeline-item review-timeline-input" styleName="review-input">
      <UserAvatar user={user} />
      <div className="i-timeline-item-box footer-only header-indicator-left">
        <div className="i-box-footer" style={{overflow: 'visible'}}>
          {renderForm()}
        </div>
      </div>
    </div>
  );
}
