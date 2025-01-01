// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';

import {DailyTimelineContent} from '../timeline';

import '../../components/WeekdayInformation.module.scss';
import './DummyTimeline.module.scss';

export function DummyTimeline({rows}) {
  const currentDate = moment();
  const dummyData = Array(rows)
    .fill()
    .map((_, i) => {
      const date = currentDate.clone().add(i, 'days');
      return {
        availability: {
          candidates: [
            {
              startDt: date.set({hour: 9, minute: 0, second: 0}).format(),
              endDt: date.set({hour: 11, minute: 0, second: 0}).format(),
              bookable: false,
            },
          ],
          conflictingCandidates: [],
        },
        key: date.format('YYYY-MM-DD'),
        room: {
          id: null,
          name: 'Dummy Room',
        },
        label: (
          <>
            <span styleName="weekday">{date.format('ddd')}</span> {date.format('L')}
          </>
        ),
      };
    });

  return (
    <div styleName="blurred-timeline">
      <DailyTimelineContent rows={dummyData} />
    </div>
  );
}

export default DummyTimeline;

DummyTimeline.propTypes = {
  rows: PropTypes.number.isRequired,
};

DummyTimeline.defaultProps = {};
