// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import RevisionComment from './RevisionComment';
import RevisionJudgment from './RevisionJudgment';
import RevisionReview from './RevisionReview';

function renderTimelineItem(item, revision) {
  if (item.timelineItemType === 'judgment') {
    return <RevisionJudgment key={`${item.createdDt}-${revision.id}`} revision={revision} />;
  } else if (item.timelineItemType === 'comment') {
    return <RevisionComment key={item.id} revision={revision} comment={item} />;
  } else if (item.timelineItemType === 'review') {
    return <RevisionReview key={item.id} review={item} revision={revision} />;
  }
}

export default function RevisionTimeline({revision}) {
  return revision.timeline.map(item => renderTimelineItem(item, revision));
}

RevisionTimeline.propTypes = {
  revision: PropTypes.object.isRequired,
};
