// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';
import {Calendar, momentLocalizer} from 'react-big-calendar';
import withDragAndDrop from 'react-big-calendar/lib/addons/dragAndDrop';
import {useDispatch, useSelector} from 'react-redux';

import {toClasses} from 'indico/react/util';

import * as actions from './actions';
import {entryStyleGetter, layoutAlgorithm} from './layout';
import * as selectors from './selectors';
import Toolbar from './Toolbar';

import 'react-big-calendar/lib/addons/dragAndDrop/styles.scss';

import './Timetable.module.scss';

const localizer = momentLocalizer(moment);
const DnDCalendar = withDragAndDrop(Calendar);

export default function Timetable() {
  const dispatch = useDispatch();
  const compactMode = useSelector(selectors.isCompactModeEnabled);
  const entries = useSelector(selectors.getAllEntries);
  const numColumns = Math.max(...entries.map(e => e.resourceId)) || 1;

  const defaultDate = entries.reduce(
    (min, {start}) => (start < min ? start : min),
    entries[0].start
  );

  const minHour = entries.reduce((min, {start}) => {
    const hours = start.getHours();
    if (hours > min) {
      return min;
    }
    return start.getMinutes() === 0 ? hours - 1 : hours;
  }, 9);

  const maxHour = entries.reduce((max, {end}) => {
    const hours = end.getHours();
    if (hours < max - 1) {
      return max;
    }
    return end.getMinutes() === 0 ? hours + 1 : hours + 2;
  }, 17);

  return (
    <DnDCalendar
      styleName={toClasses({timetable: true, compact: compactMode})}
      defaultDate={defaultDate}
      defaultView="day"
      events={entries}
      localizer={localizer}
      views={{day: true}}
      components={{toolbar: Toolbar}}
      resources={[...Array(numColumns).keys()].map(n => ({id: n + 1}))}
      onEventDrop={args => dispatch(actions.moveEntry(args))}
      onEventResize={args => dispatch(actions.resizeEntry(args))}
      onSelectSlot={(...args) => console.debug('onSelectSlot', ...args)}
      eventPropGetter={entryStyleGetter(entries)}
      dayLayoutAlgorithm={layoutAlgorithm(entries, numColumns, compactMode)}
      allDayMaxRows={0}
      step={5}
      timeslots={6}
      min={new Date(1972, 0, 1, minHour, 0, 0)}
      max={new Date(1972, 0, 1, maxHour, 0, 0)}
      tooltipAccessor={null}
      resizable
      selectable
    />
  );
}
