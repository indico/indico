// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React, {useEffect, useMemo, useRef} from 'react';
import {useDispatch} from 'react-redux';

import './DayTimetable.module.scss';
import * as actions from './actions';
import {TimeGutter, Lines} from './DayTimetable';
import {createRestrictToElement, Transform, Over, MousePosition, UniqueId} from './dnd';
import {useDroppable, DnDProvider} from './dnd/dnd';
import {DraggableBlockEntry, DraggableEntry} from './Entry';
import {computeYoffset, getGroup, layout, layoutGroupAfterMove} from './layout';
import {TopLevelEntry} from './types';
import UnscheduledContributions from './UnscheduledContributions';
import {minutesToPixels, pixelsToMinutes} from './utils';

export function WeekTimetable({
  entries,
  minHour,
  maxHour,
  offset,
  weekLength,
}: {
  entries: Record<string, TopLevelEntry[]>;
  minHour: number;
  maxHour: number;
  offset: number;
  weekLength: number;
}) {
  const dispatch = useDispatch();
  const mouseEventRef = useRef<MouseEvent | null>(null);
  const calendarRef = useRef<HTMLDivElement | null>(null);

  const days = useMemo(() => {
    const allDays = Object.keys(entries);
    const startDay = moment(allDays[0]).add(offset, 'days');
    return Array.from({length: 7}, (_, i) =>
      startDay
        .clone()
        .add(i, 'days')
        .format('YYYYMMDD')
    );
  }, [entries, offset]);

  const filteredEntries = useMemo(
    () => Object.fromEntries(days.map(dt => [dt, computeYoffset(entries[dt] || [], minHour)])),
    [entries, days, minHour]
  );

  const setDurations = useMemo(() => {
    const obj = {};
    for (const dt in filteredEntries) {
      obj[dt] = {};
      for (const e of filteredEntries[dt]) {
        obj[dt][e.id] = (duration: number) => dispatch(actions.resizeEntry(dt, e.id, duration));
      }
    }
    return obj;
  }, [filteredEntries, dispatch]);

  const setChildDurations = useMemo(() => {
    const obj = {};
    for (const dt in filteredEntries) {
      obj[dt] = {};
      for (const e of filteredEntries[dt]) {
        obj[dt][e.id] = (id: number) => (duration: number) =>
          dispatch(actions.resizeEntry(dt, id, duration, e.id));
      }
    }
    return obj;
  }, [filteredEntries, dispatch]);

  function handleDragEnd(who: string, over: Over[], delta: Transform, mouse: MousePosition) {
    if (over.length === 0) {
      return;
    }
    const days = Object.keys(filteredEntries);

    // Cannot drop on itself
    over = over.filter(o => o.id !== who);

    const day = over.find(o => days.includes(o.id));
    if (!day) {
      return;
    }

    handleDropOnDay(who, day, delta, mouse);
  }

  function handleDropOnDay(who: UniqueId, over: Over, delta: Transform, mouse: MousePosition) {
    const [from, to] = layoutAfterDropOnDay(filteredEntries, who, over, delta, mouse) || [];
    if (!from) {
      return;
    }
    if (from.dt === to.dt) {
      dispatch(actions.moveEntry(moment(from.dt).format('YYYYMMDD'), from.layout));
    } else {
      dispatch(actions.moveEntry(moment(from.dt).format('YYYYMMDD'), from.layout));
      dispatch(actions.moveEntry(moment(to.dt).format('YYYYMMDD'), to.layout));
    }
  }

  useEffect(() => {
    function onMouseMove(event: MouseEvent) {
      mouseEventRef.current = event;
    }

    document.addEventListener('mousemove', onMouseMove);
    return () => {
      document.removeEventListener('mousemove', onMouseMove);
    };
  }, []);

  const restrictToCalendar = useMemo(() => createRestrictToElement(calendarRef), [calendarRef]);
  const dayComponents = days.map((dt, i) => {
    const isWithinEvent = entries.hasOwnProperty(dt);
    return (
      <DnDDay key={dt} dt={dt} isWithinEvent={isWithinEvent}>
        <Lines minHour={minHour} maxHour={maxHour} first={i === 0} />
        {isWithinEvent &&
          filteredEntries[dt].map(entry =>
            entry.type === 'block' ? (
              <DraggableBlockEntry
                key={entry.id}
                renderChildren={false}
                setDuration={setDurations[dt][entry.id]}
                setChildDuration={setChildDurations[dt][entry.id]}
                {...entry}
              />
            ) : (
              <DraggableEntry key={entry.id} {...entry} setDuration={setDurations[dt][entry.id]} />
            )
          )}
      </DnDDay>
    );
  });

  return (
    <DnDProvider onDrop={handleDragEnd} modifier={restrictToCalendar}>
      <UnscheduledContributions />
      <div className="wrapper">
        <div styleName="wrapper">
          <TimeGutter minHour={minHour} maxHour={maxHour} />
          <div ref={calendarRef} style={{display: 'flex', width: '100%', marginTop: 10}}>
            {dayComponents}
          </div>
        </div>
      </div>
    </DnDProvider>
  );
}

function DnDDay({
  dt,
  children,
  isWithinEvent,
}: {
  dt: string;
  children: React.ReactNode;
  isWithinEvent: boolean;
}) {
  const {setNodeRef} = useDroppable({
    id: dt,
  });

  return (
    <div ref={setNodeRef} styleName={`calendar day ${isWithinEvent ? '' : 'greyed-out'}`}>
      {children}
    </div>
  );
}

function layoutAfterDropOnDay(
  entries: Record<string, TopLevelEntry[]>,
  who: UniqueId,
  over: Over,
  delta: Transform,
  mouse: MousePosition
) {
  const id = parseInt(who, 10);
  const {x, y} = delta;
  const deltaMinutes = Math.ceil(pixelsToMinutes(y) / 5) * 5;
  const mousePosition = (mouse.x - over.rect.left) / over.rect.width;

  let entry, fromDay: string | undefined;
  for (const dt in entries) {
    entry = entries[dt].find(e => e.id === id);
    if (entry) {
      fromDay = dt;
      break;
    }
  }

  if (!entry) {
    return;
  }

  // create a new moment object from entry.startDt but change the day to the day of over.id
  const newStartDt = moment(over.id).set({
    hour: moment(entry.startDt).hour(),
    minute: moment(entry.startDt).minute(),
  });

  entry = {
    ...entry,
    startDt: moment(newStartDt).add(deltaMinutes, 'minutes'),
    x: entry.x + x,
    y: minutesToPixels(
      moment(newStartDt)
        .add(deltaMinutes, 'minutes')
        .diff(moment(newStartDt).startOf('day'), 'minutes')
    ),
  };
  if (entry.type === 'block') {
    entry = {
      ...entry,
      children: entry.children.map(e => ({
        ...e,
        startDt: moment(over.id)
          .set({
            hour: moment(e.startDt).hour(),
            minute: moment(e.startDt).minute(),
          })
          .add(deltaMinutes, 'minutes'),
      })),
    };
  }

  const toEntries = entries[over.id];
  const groupIds = getGroup(entry, toEntries.filter(e => e.id !== entry.id));
  let group = toEntries.filter(e => groupIds.has(e.id));
  group = layoutGroupAfterMove(group, entry, mousePosition);

  const otherEntries = toEntries.filter(e => !groupIds.has(e.id) && e.id !== entry.id);
  const newLayout = layout([...otherEntries, ...group]);

  if (fromDay === over.id) {
    return [{layout: newLayout, dt: fromDay}, {layout: newLayout, dt: fromDay}];
  } else {
    const fromEntries = entries[fromDay].filter(e => e.id !== entry.id);
    const newFromLayout = layout(fromEntries);
    return [{layout: newFromLayout, dt: fromDay}, {layout: newLayout, dt: over.id}];
  }
}
