// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import React, {useEffect, useMemo, useRef} from 'react';
import {useDispatch, useSelector} from 'react-redux';

import './DayTimetable.module.scss';
import * as actions from './actions';
import {createRestrictToElement, Transform, Over, MousePosition, UniqueId} from './dnd';
import {useDroppable, DnDProvider} from './dnd/dnd';
import {DraggableBlockEntry, DraggableEntry} from './Entry';
import {computeYoffset, getGroup, layout, layoutGroupAfterMove} from './layout';
import * as selectors from './selectors';
import {TopLevelEntry, BlockEntry} from './types';
import UnscheduledContributions from './UnscheduledContributions';
import {minutesToPixels, pixelsToMinutes} from './utils';

interface DayTimetableProps {
  dt: Moment;
  minHour: number;
  maxHour: number;
  entries: TopLevelEntry[];
}

function TopLevelEntries({dt, entries}: {dt: Moment; entries: TopLevelEntry[]}) {
  const dispatch = useDispatch();
  const selectedId = useSelector(selectors.getSelectedId);

  const setDurations = useMemo(() => {
    const obj = {};
    for (const e of entries) {
      obj[e.id] = (duration: number) =>
        dispatch(actions.resizeEntry(dt.format('YYYYMMDD'), e.id, duration));
    }
    return obj;
  }, [entries, dispatch, dt]);

  const setChildDurations = useMemo(() => {
    const obj = {};
    for (const e of entries) {
      obj[e.id] = (id: number) => (duration: number) =>
        dispatch(actions.resizeEntry(dt.format('YYYYMMDD'), id, duration, e.id));
    }
    return obj;
  }, [entries, dispatch, dt]);

  return (
    <>
      {entries.map(entry =>
        entry.type === 'block' ? (
          <DraggableBlockEntry
            key={entry.id}
            selected={selectedId === entry.id}
            // setDuration={setDuration}
            setDuration={setDurations[entry.id]}
            setChildDuration={setChildDurations[entry.id]}
            {...entry}
          />
        ) : (
          <DraggableEntry key={entry.id} setDuration={setDurations[entry.id]} {...entry} />
        )
      )}
    </>
  );
}

const MemoizedTopLevelEntries = React.memo(TopLevelEntries);

export function DayTimetable({dt, minHour, maxHour, entries}: DayTimetableProps) {
  const dispatch = useDispatch();
  const mouseEventRef = useRef<MouseEvent | null>(null);
  const unscheduled = useSelector(selectors.getUnscheduled);
  const calendarRef = useRef<HTMLDivElement | null>(null);

  entries = useMemo(() => computeYoffset(entries, minHour), [entries, minHour]);

  function handleDragEnd(who: string, over: Over[], delta: Transform, mouse: MousePosition) {
    if (over.length === 0) {
      return;
    }

    // if (who.startsWith('unscheduled-')) {
    //   handleUnscheduledDrop(who, over[0], delta, mouse);
    // }

    // Cannot drop on itself
    over = over.filter(o => o.id !== who);

    const calendar = over.find(o => o.id === 'calendar');
    if (!calendar) {
      return;
    }

    if (over.length === 1) {
      handleDropOnCalendar(who, calendar, delta, mouse);
    } else {
      const block = over.find(o => o.id !== 'calendar');
      if (block) {
        handleDropOnBlock(who, block, delta, mouse, calendar);
      }
    }
  }

  function handleUnscheduledDrop(
    who: UniqueId,
    over: Over,
    delta: Transform,
    mouse: MousePosition
  ) {
    const [newLayout, newUnscheduled] =
      layoutAfterUnscheduledDrop(dt, unscheduled, entries, who, over, delta, mouse) || [];
    if (!newLayout) {
      return;
    }
    dispatch(actions.scheduleEntry(dt.format('YYYYMMDD'), newLayout, newUnscheduled));
  }

  function handleDropOnCalendar(who: UniqueId, over: Over, delta: Transform, mouse: MousePosition) {
    const newLayout = layoutAfterDropOnCalendar(entries, who, over, delta, mouse);
    if (!newLayout) {
      return;
    }
    dispatch(actions.moveEntry(dt.format('YYYYMMDD'), newLayout));
  }

  function handleDropOnBlock(
    who: UniqueId,
    over: Over,
    delta: Transform,
    mouse: MousePosition,
    calendar: Over
  ) {
    const newLayout = layoutAfterDropOnBlock(entries, who, over, delta, mouse, calendar);
    if (!newLayout) {
      return;
    }
    dispatch(actions.moveEntry(dt.format('YYYYMMDD'), newLayout));
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

  return (
    <DnDProvider onDrop={handleDragEnd} modifier={restrictToCalendar}>
      <UnscheduledContributions />
      <div className="wrapper">
        <div styleName="wrapper">
          <TimeGutter minHour={minHour} maxHour={maxHour} />
          <DnDCalendar>
            <div ref={calendarRef}>
              <Lines minHour={minHour} maxHour={maxHour} />
              <MemoizedTopLevelEntries dt={dt} entries={entries} />
            </div>
          </DnDCalendar>
        </div>
      </div>
    </DnDProvider>
  );
}

interface TimeGutterProps {
  minHour: number;
  maxHour: number;
}

export function Lines({
  minHour,
  maxHour,
  first = true,
}: {
  minHour: number;
  maxHour: number;
  first: boolean;
}) {
  const oneHour = minutesToPixels(60);

  return (
    <div styleName={`lines ${first ? 'first' : ''}`}>
      {Array.from({length: maxHour - minHour + 1}, (_, i) => (
        <div key={i} style={{height: oneHour}} styleName="line" />
      ))}
    </div>
  );
}

export function TimeGutter({minHour, maxHour}: TimeGutterProps) {
  const oneHour = minutesToPixels(60);

  return (
    <div styleName="time-gutter">
      <div style={{height: 10}} />
      {Array.from({length: maxHour - minHour + 1}, (_, i) => (
        <TimeSlot key={i} height={oneHour} time={`${minHour + i}:00`} />
      ))}
    </div>
  );
}

function TimeSlot({height, time}: {height: number; time: string}) {
  return (
    <div styleName="time-slot" style={{height}}>
      <div>{time}</div>
    </div>
  );
}

function DnDCalendar({children}: {children: React.ReactNode}) {
  const {setNodeRef} = useDroppable({
    id: 'calendar',
  });

  return (
    <div ref={setNodeRef} styleName="calendar" style={{marginTop: 10}}>
      {children}
    </div>
  );
}

function layoutAfterDropOnCalendar(
  entries: TopLevelEntry[],
  who: UniqueId,
  over: Over,
  delta: Transform,
  mouse: MousePosition
) {
  const id = parseInt(who, 10);
  const {x, y} = delta;
  const deltaMinutes = Math.ceil(pixelsToMinutes(y) / 5) * 5;
  const mousePosition = (mouse.x - over.rect.left) / over.rect.width;

  let entry = entries.find(e => e.id === id);
  let fromBlock: BlockEntry | undefined;
  if (!entry) {
    // maybe a break from inside a block
    fromBlock = entries
      .filter(e => e.type === 'block')
      .find(b => b.children.find(c => c.id === id));

    if (!fromBlock) {
      return;
    }

    entry = fromBlock.children.find(c => c.id === id);
    if (!entry || entry.type !== 'break') {
      return;
    }
  }

  if (entry.type === 'contrib' && entry.sessionId) {
    return; // contributions with sessions assigned cannot be scheduled at the top level
  }

  entry = {
    ...entry,
    startDt: moment(entry.startDt).add(deltaMinutes, 'minutes'),
    x: entry.x + x,
    y: minutesToPixels(
      moment(entry.startDt)
        .add(deltaMinutes, 'minutes')
        .diff(moment(entry.startDt).startOf('day'), 'minutes')
    ),
  };
  if (entry.type === 'block') {
    entry = {
      ...entry,
      children: entry.children.map(e => ({
        ...e,
        startDt: moment(e.startDt).add(deltaMinutes, 'minutes'),
      })),
    };
  }

  const groupIds = getGroup(entry, entries.filter(e => e.id !== entry.id));
  let group = entries.filter(e => groupIds.has(e.id));
  group = layoutGroupAfterMove(group, entry, mousePosition);

  if (!fromBlock) {
    const otherEntries = entries.filter(e => !groupIds.has(e.id) && e.id !== entry.id);
    return layout([...otherEntries, ...group]);
  } else {
    const otherEntries = entries.filter(
      e => !groupIds.has(e.id) && e.id !== entry.id && e.id !== fromBlock.id
    );
    const fromChildren = fromBlock.children.filter(e => e.id !== entry.id);
    group = group.filter(e => e.id !== fromBlock.id); // might contain the block
    return layout([...otherEntries, ...group, {...fromBlock, children: fromChildren}]);
  }
}

function layoutAfterDropOnBlock(
  entries: TopLevelEntry[],
  who: UniqueId,
  over: Over,
  delta: Transform,
  mouse: MousePosition,
  calendar: Over
) {
  const id = parseInt(who, 10);
  const overId = parseInt(over.id, 10);
  const toBlock = entries.find(e => e.id === overId);

  if (!toBlock || toBlock.type !== 'block') {
    return;
  }

  const fromBlock = entries
    .filter(e => e.type === 'block')
    .find(entry => !!entry.children.find(c => c.id === id));

  const {x, y} = delta;
  const deltaMinutes = Math.ceil(pixelsToMinutes(y) / 5) * 5;
  const mousePosition = (mouse.x - over.rect.left) / over.rect.width;

  let entry: TopLevelEntry | undefined;
  if (!fromBlock) {
    entry = entries.find(e => e.id === id);
    if (!entry) {
      return;
    }
  } else {
    entry = fromBlock.children.find(e => e.id === id);
  }

  if (!entry) {
    return;
  }

  if (entry.type === 'contrib') {
    if (!entry.sessionId) {
      // Allow top level contributions being dropped on blocks to be treated as if they
      // were dropped directly on the calendar instead
      return layoutAfterDropOnCalendar(entries, who, calendar, delta, mouse);
    }
    if (entry.sessionId !== toBlock.sessionId) {
      return; // contributions cannot be moved to blocks of different sessions
    }
  } else if (entry.type === 'block') {
    // Allow blocks being dropped on other blocks to be treated as if they
    // were dropped directly on the calendar instead
    return layoutAfterDropOnCalendar(entries, who, calendar, delta, mouse);
  }

  if (entry.duration > toBlock.duration) {
    return; // TODO: auto-resize the block?
  }

  entry = {
    ...entry,
    startDt: moment(entry.startDt).add(deltaMinutes, 'minutes'),
    x: entry.x + x,
    y: minutesToPixels(
      moment(entry.startDt)
        .add(deltaMinutes, 'minutes')
        .diff(moment(toBlock.startDt), 'minutes')
    ),
  };

  if (entry.startDt.isBefore(moment(toBlock.startDt))) {
    // move start time to the start of the block
    entry.startDt = moment(toBlock.startDt);
  } else if (
    moment(entry.startDt)
      .add(entry.duration, 'minutes')
      .isAfter(moment(toBlock.startDt).add(toBlock.duration, 'minutes'))
  ) {
    // move end time to the end of the block
    entry.startDt = moment(toBlock.startDt).add(toBlock.duration - entry.duration, 'minutes');
  }

  const groupIds = getGroup(entry, toBlock.children.filter(e => e.id !== entry.id));
  let group = toBlock.children.filter(e => groupIds.has(e.id));
  group = layoutGroupAfterMove(group, entry, mousePosition);

  const otherChildren = toBlock.children.filter(e => !groupIds.has(e.id) && e.id !== entry.id);

  if (!fromBlock) {
    return layout([
      ...entries.filter(e => e.id !== entry.id && e.id !== toBlock.id),
      {...toBlock, children: [...otherChildren, ...group]},
    ]);
  } else if (toBlock.id === fromBlock.id) {
    const otherEntries = entries.filter(e => e.id !== toBlock.id);
    return layout([...otherEntries, {...toBlock, children: [...otherChildren, ...group]}]);
  } else {
    const otherEntries = entries.filter(e => e.id !== toBlock.id && e.id !== fromBlock.id);
    const fromChildren = fromBlock.children.filter(e => e.id !== entry.id);
    return layout([
      ...otherEntries,
      {...fromBlock, children: fromChildren},
      {...toBlock, children: [...otherChildren, ...group]},
    ]);
  }
}

function layoutAfterUnscheduledDrop(
  dt: Moment,
  unscheduled: TopLevelEntry[],
  entries: TopLevelEntry[],
  who: UniqueId,
  over: Over,
  delta: Transform,
  mouse: MousePosition
) {
  const id = parseInt(who.slice('unscheduled-'.length), 10);
  const {x, y} = delta;
  const deltaMinutes = Math.ceil(pixelsToMinutes(y) / 5) * 5;
  const mousePositionX = (mouse.x - over.rect.left) / over.rect.width;
  const mousePositionY = mouse.y - over.rect.top - window.scrollY;

  const startDt = moment(dt)
    .startOf('day')
    .add(Math.ceil(pixelsToMinutes(mousePositionY) / 5) * 5, 'minutes');

  let entry = unscheduled.find(e => e.id === id);
  if (!entry) {
    return;
  }
  entry = {
    ...entry,
    startDt,
    x,
    y: minutesToPixels(
      moment(startDt)
        .add(deltaMinutes, 'minutes')
        .diff(moment(entry.startDt).startOf('day'), 'minutes')
    ),
  };

  const groupIds = getGroup(entry, entries);
  let group = entries.filter(e => groupIds.has(e.id));
  group = layoutGroupAfterMove(group, entry, mousePositionX);

  const otherEntries = entries.filter(e => !groupIds.has(e.id) && e.id !== entry.id);
  return [layout([...otherEntries, ...group]), unscheduled.filter(e => e.id !== id)];
}
