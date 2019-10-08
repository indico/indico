// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';

import RevisionJudgment from './RevisionJudgment';
import RevisionComment from './RevisionComment';
import RevisionReview from './RevisionReview';

function renderTimelineItem(item, revision) {
  if (item.timelineItemType === 'judgment') {
    return <RevisionJudgment key={`${item.createdDt}-${revision.id}`} revision={revision} />;
  } else if (item.timelineItemType === 'comment') {
    return <RevisionComment key={item.id} revision={revision} comment={item} />;
  } else if (item.timelineItemType === 'review') {
    return <RevisionReview key={item.id} review={item} />;
  }
}

export default function RevisionTimeline({revision}) {
  const timeline = revision.timeline;

  return (
    <div className="i-timeline with-line">
      <div className="i-timeline-connect-up" />
      {timeline.map(item => renderTimelineItem(item, revision))}
    </div>
  );
}

RevisionTimeline.propTypes = {
  revision: PropTypes.object.isRequired,
};
