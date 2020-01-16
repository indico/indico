// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';
import {useSelector} from 'react-redux';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';
import {getPaperDetails} from '../selectors';

export default function RevisionReview({review}) {
  const {
    ratingRange: [, maxScore],
  } = useSelector(getPaperDetails);
  const wrapper = (
    <span className={`bold underline semantic-text ${review.proposedAction.cssClass}`} />
  );

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
            <i
              className={`review-comment-visibility ${review.visibility.name} icon-shield`}
              title={review.visibility.title}
            />{' '}
            <time dateTime={serializeDate(review.createdDt, moment.HTML5_FMT.DATETIME_LOCAL)}>
              {serializeDate(review.createdDt, 'LL')}
            </time>
            {review.modifiedDt && (
              <>
                {' '}
                ·{' '}
                <span
                  className="review-comment-edited"
                  title={serializeDate(review.modifiedDt, 'LL')}
                >
                  <Translate>edited</Translate>
                </span>
              </>
            )}
          </div>
          <div className="review-group truncate-text">
            <span title={review.group.title}>{review.group.title}</span>
          </div>
        </div>
        <div
          data-no-comment={!review.comment}
          className={`i-timeline-item-box header-indicator-top ${
            !review.comment ? 'header-only' : ''
          }`}
        >
          <div className="i-box-header flexrow">
            <div className="review-badges">
              {review.proposedAction.name === 'accept' && (
                <Translate>
                  Proposed to <Param name="actionName" value="accept" wrapper={wrapper} />
                </Translate>
              )}
              {review.proposedAction.name === 'reject' && (
                <Translate>
                  Proposed to <Param name="actionName" value="reject" wrapper={wrapper} />
                </Translate>
              )}
              {review.proposedAction.name === 'to_be_corrected' && (
                <Translate>
                  Proposed to <Param name="actionName" value="correct" wrapper={wrapper} />
                </Translate>
              )}{' '}
              {review.ratings.length > 0 &&
                (review.score !== null && (
                  <>
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
                    {' ('}
                    <a className="toggle-link">
                      <span>
                        <Translate>show ratings</Translate>
                      </span>
                      <span className="weak-hidden">
                        <Translate>hide ratings</Translate>
                      </span>
                    </a>
                    )
                  </>
                ))}
            </div>
          </div>
          <div className="i-box-content">
            {review.comment && (
              <div
                className="markdown-text"
                dangerouslySetInnerHTML={{__html: review.commentHtml}}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

RevisionReview.propTypes = {
  review: PropTypes.object.isRequired,
};
