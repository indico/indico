// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import React from 'react';

import {useTimetableSelector} from './hooks';
import * as selectors from './selectors';

import './WeekViewToolbar.module.scss';

export default function Toolbar({
  date,
  onNavigate,
}: {
  date: Moment;
  onNavigate: (dt: Moment) => void;
}) {
  const eventStart = useTimetableSelector(selectors.getEventStartDt);
  const numDays = useTimetableSelector(selectors.getEventNumDays);
  const offset = useTimetableSelector(selectors.getNavbarOffset);

  const getDateFromIdx = idx => moment(eventStart).add(idx, 'days');

  return (
    <div style={{marginLeft: 50, display: 'flex', fontSize: 18, paddingBottom: 10}}>
      {[...Array(numDays).keys()].map(n => {
        const d = getDateFromIdx(n + offset);
        return (
          <div key={n} style={{flexGrow: 1, textAlign: 'center'}}>
            {d.format('ddd DD/MM')}
          </div>
        );
      })}
    </div>
  );
}
