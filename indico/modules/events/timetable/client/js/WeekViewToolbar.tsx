// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import React from 'react';
import {useSelector} from 'react-redux';
import {Icon} from 'semantic-ui-react';

import * as selectors from './selectors';

import './WeekViewToolbar.module.scss';

export default function WeekViewToolbar({
  date,
  onNavigate,
  onOffsetChange,
  offset,
}: {
  date: Moment;
  onNavigate: (dt: Moment) => void;
  onOffsetChange: (offset: number) => void;
  offset: number;
}) {
  const eventStart = useSelector(selectors.getEventStartDt);
  const numDays = useSelector(selectors.getEventNumDays);
  const WEEK_LENGTH = 7; // Default week length

  const isPrevDisabled = offset === 0;
  const isNextDisabled = offset + WEEK_LENGTH >= numDays;

  const getDateFromIdx = idx => moment(eventStart).add(idx, 'days');

  const handlePrevWeek = () => {
    if (isPrevDisabled) {
      return;
    }
    const newOffset = Math.max(0, offset - WEEK_LENGTH);
    onOffsetChange(newOffset);
  };

  const handleNextWeek = () => {
    if (isNextDisabled) {
      return;
    }
    const newOffset = Math.min(numDays - 1, offset + WEEK_LENGTH);
    onOffsetChange(newOffset);
  };

  return (
    <div styleName="toolbar" className="ui">
      <Icon
        name="chevron left"
        onClick={handlePrevWeek}
        styleName={`${isPrevDisabled ? 'navigation-disabled' : 'navigation-chevron'}`}
      />
      {[...Array(WEEK_LENGTH).keys()].map(n => {
        const d = getDateFromIdx(n + offset);
        const isWithinEvent = n + offset < numDays;
        const isWeekend = d.isoWeekday() > 5;
        console.log(isWithinEvent);
        return (
          <div
            key={n}
            style={{
              flexGrow: 1,
              textAlign: 'center',
              color: isWithinEvent ? 'black' : 'lightgray',
            }}
            styleName="weekdays"
          >
            <div styleName={`weekday ${isWeekend && isWithinEvent ? 'weekend' : ''}`}>
              {d.format('ddd ')}
            </div>
            {d.format('DD/MM')}
          </div>
        );
      })}
      <Icon
        name="chevron right"
        onClick={handleNextWeek}
        styleName={`${isNextDisabled ? 'navigation-disabled' : 'navigation-chevron'}`}
      />
    </div>
  );
}
