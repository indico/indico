// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';

import TimelineItem from './TimelineItem';

export default function TimelineContent({revisions, state}) {
  return revisions.map((revision, index) => {
    const isLastRevision = index === revisions.length - 1;

    return (
      <React.Fragment key={revision.id}>
        {index !== 0 && (
          <div className="i-timeline">
            <div className="i-timeline to-separator-wrapper">
              <div className="i-timeline-connect-down to-separator" />
            </div>
          </div>
        )}
        <TimelineItem revision={revision} isLastRevision={isLastRevision} state={state} />
      </React.Fragment>
    );
  });
}

TimelineContent.propTypes = {
  revisions: PropTypes.array.isRequired,
  state: PropTypes.object.isRequired,
};
