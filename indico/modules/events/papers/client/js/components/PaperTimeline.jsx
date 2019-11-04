// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useSelector} from 'react-redux';

import {getPaperDetails} from '../selectors';

import TimelineItem from './TimelineItem';

export default function PaperTimeline() {
  const {revisions} = useSelector(getPaperDetails);

  return revisions.map((revision, index) => {
    return (
      <React.Fragment key={revision.id}>
        {index !== 0 && (
          <div className="i-timeline">
            <div className="i-timeline to-separator-wrapper">
              <div className="i-timeline-connect-down to-separator" />
            </div>
          </div>
        )}
        <TimelineItem revision={revision} />
      </React.Fragment>
    );
  });
}
