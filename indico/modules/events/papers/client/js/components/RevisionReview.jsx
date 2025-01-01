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
import {Popup, Transition} from 'semantic-ui-react';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {ReviewRating} from 'indico/react/components';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import {updateReview as updateReviewAction} from '../actions';
import {getPaperDetails} from '../selectors';

import GroupReviewForm from './GroupReviewForm';

export default function RevisionReview({review, revision}) {
  const [isEditing, setIsEditing] = useState(false);
  const [showRatings, setShowRatings] = useState(false);
  const dispatch = useDispatch();
  const {
    contribution: {id: contributionId},
    event: {
      id: eventId,
      cfp: {
        ratingRange: [minScore, maxScore],
      },
    },
  } = useSelector(getPaperDetails);
  const wrapper = (
    <span className={`bold underline semantic-text ${review.proposedAction.cssClass}`} />
  );
  const renderQuestionAnswer = rating => {
    if (rating.question.fieldType === 'bool') {
      if (rating.value !== null) {
        return rating.value ? Translate.string('Yes') : Translate.string('No');
      }
      return null;
    } else if (rating.question.fieldType === 'rating') {
      return <ReviewRating min={minScore} max={maxScore} value={rating.value} disabled />;
    } else {
      return rating.value;
    }
  };
  const updateReview = async formData => {
    const rv = await dispatch(
      updateReviewAction(eventId, contributionId, revision.id, review.id, formData)
    );
    if (rv.error) {
      return rv.error;
    }
    setIsEditing(false);
  };

  return (
    <div id={`proposal-review-${review.id}`} className="i-timeline-item">
      <UserAvatar user={review.user} />
      <div className="flexrow i-timeline-item-content">
        <div className="i-timeline-item-metadata">
          <div className="f-self-stretch">
            <Translate>
              <Param name="reviewerName" value={review.user.fullName} wrapper={<strong />} /> left a
              review
            </Translate>{' '}
            <Popup
              trigger={
                <i className={`review-comment-visibility ${review.visibility.name} icon-shield`} />
              }
              content={review.visibility.title}
              position="bottom center"
            />{' '}
            <time
              dateTime={serializeDate(review.createdDt, moment.HTML5_FMT.DATETIME_LOCAL_SECONDS)}
            >
              {serializeDate(review.createdDt, 'LL')}
            </time>
            {review.modifiedDt && (
              <>
                {' '}
                ·{' '}
                <Popup
                  trigger={
                    <span className="review-comment-edited">
                      <Translate>edited</Translate>
                    </span>
                  }
                  content={serializeDate(review.modifiedDt, 'LL')}
                  position="bottom center"
                />
              </>
            )}
          </div>
          <div className="review-group truncate-text">
            <span>{review.group.title}</span>
          </div>
        </div>
        <div
          data-no-comment={!review.comment}
          className={`i-timeline-item-box header-indicator-top ${
            !review.comment && !showRatings && !isEditing ? 'header-only' : ''
          }`}
        >
          {!isEditing && (
            <div className="i-box-header flexrow">
              <div className="review-badges">
                {review.proposedAction.name === 'accept' && (
                  <Translate>
                    Proposed to{' '}
                    <Param name="actionName" wrapper={wrapper}>
                      accept
                    </Param>
                  </Translate>
                )}
                {review.proposedAction.name === 'reject' && (
                  <Translate>
                    Proposed to{' '}
                    <Param name="actionName" wrapper={wrapper}>
                      reject
                    </Param>
                  </Translate>
                )}
                {review.proposedAction.name === 'to_be_corrected' && (
                  <Translate>
                    Proposed to{' '}
                    <Param name="actionName" wrapper={wrapper}>
                      correct
                    </Param>
                  </Translate>
                )}{' '}
                {review.ratings.length > 0 && (
                  <>
                    {review.score !== null && (
                      <Translate>
                        · score{' '}
                        <Param
                          name="prettyScore"
                          value={review.score}
                          wrapper={
                            <span
                              className="highlight bold semantic-text"
                              title={Translate.string('Score: {score} / {maxScore}', {
                                score: review.score,
                                maxScore,
                              })}
                            />
                          }
                        />
                      </Translate>
                    )}
                    {' ('}
                    <a className="toggle-link" onClick={() => setShowRatings(!showRatings)}>
                      <span>
                        {showRatings ? (
                          <Translate>hide ratings</Translate>
                        ) : (
                          <Translate>show ratings</Translate>
                        )}
                      </span>
                    </a>
                    )
                  </>
                )}
              </div>
              {review.canEdit && (
                <div className="review-comment-actions">
                  <Popup
                    position="right center"
                    content={Translate.string('Edit review')}
                    trigger={<a className="i-link icon-edit" onClick={() => setIsEditing(true)} />}
                  />
                </div>
              )}
            </div>
          )}
          <div className="i-box-content">
            {isEditing ? (
              <GroupReviewForm
                group={review.group}
                review={review}
                onSubmit={updateReview}
                onCancel={() => setIsEditing(false)}
              />
            ) : (
              <>
                <Transition
                  visible={review.ratings.length !== 0 && showRatings}
                  animation="slide down"
                  duration={50}
                >
                  <div className="ratings-details">
                    <ul className="review-questions">
                      {review.ratings.map((rating, index) => (
                        <li key={`rating-${rating.question.id}-${rating.id}`} className="flexrow">
                          <div>
                            <span className="question-index">{index + 1}</span>
                          </div>
                          <div className="question-text f-self-stretch">
                            {rating.question.title}
                          </div>
                          <div>{renderQuestionAnswer(rating)}</div>
                        </li>
                      ))}
                    </ul>
                    {review.comment && (
                      <div className="titled-rule">
                        <Translate>Comment</Translate>
                      </div>
                    )}
                  </div>
                </Transition>
                {review.comment && (
                  <div
                    className="markdown-text"
                    dangerouslySetInnerHTML={{__html: review.commentHtml}}
                  />
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

RevisionReview.propTypes = {
  review: PropTypes.object.isRequired,
  revision: PropTypes.object.isRequired,
};
