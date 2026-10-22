// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';

import {localeUses24HourTime} from 'indico/utils/date';

import {minutesToPixels} from './utils';

import './DayTimetable.module.scss';

interface TimeGutterProps {
  minHour: number;
  maxHour: number;
}

function TimeSlot({height, time}: {height: number; time: string}) {
  return (
    <div styleName="time-slot" style={{height}}>
      {time}
    </div>
  );
}

function TimeGutter({minHour, maxHour}: TimeGutterProps) {
  const oneHour = minutesToPixels(60);
  const format = localeUses24HourTime(moment.locale().replace('_', '-')) ? 'HH:mm' : 'h A';

  return (
    <div styleName="time-gutter">
      {Array.from({length: maxHour - minHour + 1}, (_, i) => {
        const time = moment({hour: minHour + i}).format(format);

        return <TimeSlot key={i} height={oneHour} time={time} />;
      })}
    </div>
  );
}

export default React.memo(TimeGutter);
