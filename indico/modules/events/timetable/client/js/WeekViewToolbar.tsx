// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import React, {useCallback, useEffect, useRef} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Dropdown, Icon, Label, Menu, Message} from 'semantic-ui-react';

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
  const weekLength = 7; // Default week length

  const isPrevDisabled = offset === 0;
  const isNextDisabled = offset + weekLength >= numDays;

  const getDateFromIdx = idx => moment(eventStart).add(idx, 'days');

  const handlePrevWeek = () => {
    if (isPrevDisabled) {
      return;
    }
    const newOffset = Math.max(0, offset - weekLength);
    onOffsetChange(newOffset);
  };

  const handleNextWeek = () => {
    if (isNextDisabled) {
      return;
    }
    const newOffset = Math.min(numDays - 1, offset + weekLength);
    onOffsetChange(newOffset);
  };

  return (
    <div style={{display: 'flex', fontSize: 18, paddingBottom: 10}} className="ui">
      <Icon
        name="chevron left"
        onClick={handlePrevWeek}
        style={{
          cursor: isPrevDisabled ? 'not-allowed' : 'pointer',
          color: isPrevDisabled ? 'lightgray' : 'black',
        }}
      />
      {[...Array(weekLength).keys()].map(n => {
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
            <span styleName={isWeekend && isWithinEvent ? 'weekend' : ''}>{d.format('ddd ')}</span>
            {d.format('DD/MM')}
          </div>
        );
      })}
      <Icon
        name="chevron right"
        onClick={handleNextWeek}
        style={{
          cursor: isNextDisabled ? 'not-allowed' : 'pointer',
          color: isNextDisabled ? 'lightgray' : 'black',
        }}
      />
    </div>
  );
}
