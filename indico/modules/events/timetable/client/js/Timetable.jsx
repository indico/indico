// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React, {useState} from 'react';
import {Calendar, momentLocalizer} from 'react-big-calendar';
import withDragAndDrop from 'react-big-calendar/lib/addons/dragAndDrop';

import {entryStyleGetter, layoutAlgorithm, tooltipAccessor} from './layout';
import initialValues from './timetable-data';
import Toolbar from './Toolbar';
import {processEntries} from './util';

import 'react-big-calendar/lib/addons/dragAndDrop/styles.scss';

import './Timetable.module.scss';

const localizer = momentLocalizer(moment);
const DnDCalendar = withDragAndDrop(Calendar);

export default function Timetable() {
  const [_entries, _columns] = processEntries(initialValues);
  const [entries, setEntries] = useState(_entries);
  const [columns, setColumns] = useState(_columns);

  const moveEntry = ({event: entry, start, end, resourceId}) => {
    const existing = entries.find(e => e.id === entry.id) || {};
    const filtered = entries.filter(e => e.id !== entry.id);
    const newEntries = [...filtered, {...existing, start, end}];
    const [processedEntries, newColumns] = processEntries(newEntries, {
      entryId: entry.id,
      sourceResourceId: existing.resourceId,
      targetResourceId: resourceId,
    });
    setEntries(processedEntries);
    setColumns(newColumns);
  };

  const resizeEntry = ({event: entry, start, end}) => {
    const existing = entries.find(ev => ev.id === entry.id) ?? {};
    const filtered = entries.filter(ev => ev.id !== entry.id);
    const newEntries = [...filtered, {...existing, start, end}];
    const [processedEntries, newColumns] = processEntries(newEntries, {
      entryId: entry.id,
      sourceResourceId: existing.resourceId,
      targetResourceId: existing.resourceId,
    });
    setEntries(processedEntries);
    setColumns(newColumns);
  };

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
      styleName="timetable"
      defaultDate={defaultDate}
      defaultView="day"
      events={entries}
      localizer={localizer}
      views={{day: true}}
      components={{toolbar: Toolbar}}
      resources={columns}
      onEventDrop={moveEntry}
      onEventResize={resizeEntry}
      onSelectSlot={(...args) => console.debug('onSelectSlot', ...args)}
      eventPropGetter={entryStyleGetter(entries)}
      dayLayoutAlgorithm={layoutAlgorithm(entries, columns.length, true)}
      allDayMaxRows={0}
      step={5}
      timeslots={6}
      min={new Date(1972, 0, 1, minHour, 0, 0)}
      max={new Date(1972, 0, 1, maxHour, 0, 0)}
      tooltipAccessor={tooltipAccessor(entries)}
      resizable
      selectable
    />
  );
}
