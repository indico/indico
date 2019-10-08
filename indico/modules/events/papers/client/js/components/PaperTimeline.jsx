// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useSelector} from 'react-redux';

import {getPaperDetails, getPaperPermissions} from '../selectors';

import RevisionInfo from './RevisionInfo';
import RevisionJudgment from './RevisionJudgment';
import SubmitRevision from './SubmitRevision';
import RevisionTimeline from './RevisionTimeline';
import PaperReviewForm from './PaperReviewForm';

export default function PaperTimeline() {
  const {event, revisions, isInFinalState} = useSelector(getPaperDetails);
  const {canReview: canUserReview, canComment: canUserComment} = useSelector(getPaperPermissions);
  const canComment = !event.isLocked && !isInFinalState && canUserComment;
  const canReview = !event.isLocked && !isInFinalState && canUserReview;

  return revisions.map((revision, index) => {
    const timeline = revision.timeline;
    const isLastItem = index === revisions.length - 1;

    return (
      <React.Fragment key={revision.id}>
        {index !== 0 && (
          <div className="i-timeline">
            <div className="i-timeline to-separator-wrapper">
              <div className="i-timeline-connect-down to-separator" />
            </div>
          </div>
        )}
        <RevisionInfo revision={revision} />
        <div
          className={`i-timeline ${!revision.isLastRevision ? 'weak-hidden' : ''}`}
          id={`revision-timeline-${revision.id}`}
        >
          {(timeline.length > 0 || canReview || canComment) && (
            <RevisionTimeline revision={revision} />
          )}
          {index === revisions.length - 1 && (canComment || canReview) && <PaperReviewForm />}
          {isLastItem && (
            <>
              <div className="i-timeline to-separator-wrapper">
                <div className="i-timeline-connect-down to-separator" />
              </div>
              <div className="i-timeline-separator" />
              <SubmitRevision />
              {isInFinalState && <RevisionJudgment revision={revision} />}
            </>
          )}
        </div>
      </React.Fragment>
    );
  });
}
