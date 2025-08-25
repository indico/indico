// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import React, {useEffect, useMemo, useRef, useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';

import './DayTimetable.module.scss';
import * as actions from './actions';
import {Transform, Over, MousePosition} from './dnd';
import {useDroppable, DnDProvider} from './dnd/dnd';
import {createRestrictToCalendar} from './dnd/modifiers';
import {DraggableBlockEntry, DraggableEntry} from './Entry';
import {computeYoffset, getGroup, layout, layoutGroup, layoutGroupAfterMove} from './layout';
import * as selectors from './selectors';
import TimetableCreateModal from './TimetableCreateModal';
import {TopLevelEntry, BlockEntry, Entry, isChildEntry} from './types';
import UnscheduledContributions from './UnscheduledContributions';
import {GRID_SIZE_MINUTES, minutesToPixels, pixelsToMinutes, snapMinutes} from './utils';

// TODO: (Ajob) Remove when discussed how to handle pre-existing uniqueID type
type UniqueId = string;

interface DraftEntry {
  startDt: Moment;
  duration: number;
  height?: number;
  y?: number;
}

interface DayTimetableProps {
  dt: Moment;
  eventId: number;
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

export function DayTimetable({dt, eventId, minHour, maxHour, entries}: DayTimetableProps) {
  const dispatch = useDispatch();
  const mouseEventRef = useRef<MouseEvent | null>(null);
  const unscheduled = useSelector(selectors.getUnscheduled);
  const calendarRef = useRef<HTMLDivElement | null>(null);

  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState(false);
  const [newEntry, setNewEntry] = useState<DraftEntry | null>(null);

  entries = useMemo(() => computeYoffset(entries, minHour), [entries, minHour]);

  function handleDragEnd(
    who: string,
    over: Over[],
    delta: Transform,
    mouse: MousePosition,
    offset
  ) {
    if (over.length === 0) {
      return;
    }

    // Cannot drop on itself
    over = over.filter(o => o.id !== who);

    if (who.startsWith('unscheduled-')) {
      const calendar = over.find(o => o.id === 'calendar');
      if (!calendar) {
        return;
      }
      if (over.length === 1) {
        handleUnscheduledDrop(who, calendar, delta, mouse, offset);
      } else {
        const block = over.find(o => o.id !== 'calendar');
        if (block) {
          handleUnscheduledDropOnBlock(who, block, delta, mouse, offset, calendar);
        }
      }
    }

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
    mouse: MousePosition,
    offset
  ) {
    const [newLayout, newUnscheduled] =
      layoutAfterUnscheduledDrop(dt, unscheduled, entries, who, over, delta, mouse, offset) || [];
    if (!newLayout) {
      return;
    }
    dispatch(actions.scheduleEntry(dt.format('YYYYMMDD'), newLayout, newUnscheduled));
  }

  function handleUnscheduledDropOnBlock(
    who: UniqueId,
    over: Over,
    delta: Transform,
    mouse: MousePosition,
    offset,
    calendar: Over
  ) {
    const [newLayout, newUnscheduled] =
      layoutAfterUnscheduledDropOnBlock(
        dt,
        unscheduled,
        entries,
        who,
        over,
        delta,
        mouse,
        offset,
        calendar
      ) || [];
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

  useEffect(() => {
    if (!newEntry) {
      return;
    }

    function handler() {
      setIsModalOpen(true);
    }

    const calendarNode = calendarRef.current;
    calendarNode.addEventListener('click', handler);

    return () => {
      calendarNode.removeEventListener('click', handler);
    };
  }, [newEntry]);

  useEffect(() => {
    function onMouseDown(event: MouseEvent) {
      if (event.target !== calendarRef.current) {
        return;
      }

      const rect = calendarRef.current.getBoundingClientRect();
      const y = minutesToPixels(
        Math.round(pixelsToMinutes(event.clientY - rect.top) / GRID_SIZE_MINUTES) *
          GRID_SIZE_MINUTES
      );

      const startDt = moment(dt)
        .startOf('days')
        .add(minHour, 'hours')
        .add(pixelsToMinutes(y), 'minutes');

      setIsDragging(true);
      setNewEntry({
        startDt,
        duration: GRID_SIZE_MINUTES, // TODO: (Ajob) Replace with default duration
        y,
      });
    }

    function onMouseMove(event: MouseEvent) {
      if (!isDragging || !newEntry) {
        return;
      }
      const rect = calendarRef.current.getBoundingClientRect();
      const duration = Math.max(
        Math.round(pixelsToMinutes(event.clientY - rect.top - newEntry.y) / GRID_SIZE_MINUTES) *
          GRID_SIZE_MINUTES,
        GRID_SIZE_MINUTES // TODO: Replace with default duration
      );

      if (newEntry.duration === duration) {
        return;
      }

      setNewEntry({...newEntry, duration});
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsDragging(false);
        setNewEntry(null);
      }
    }

    function onMouseUp() {
      if (isDragging && newEntry) {
        setIsDragging(false);
      }
    }

    calendarRef.current.addEventListener('mousedown', onMouseDown);
    calendarRef.current.addEventListener('mousemove', onMouseMove);
    calendarRef.current.addEventListener('mouseup', onMouseUp);
    document.addEventListener('keydown', onKeyDown);

    return () => {
      calendarRef.current.removeEventListener('mousedown', onMouseDown);
      calendarRef.current.removeEventListener('mousemove', onMouseMove);
      // TODO: Fix this warning below:
      // The ref value 'calendarRef.current' will likely have changed by the time this effect cleanup function runs
      calendarRef.current.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [newEntry, dt, dispatch, isDragging, minHour]);

  const restrictToCalendar = useMemo(() => createRestrictToCalendar(calendarRef), [calendarRef]);

  return (
    <DnDProvider onDrop={handleDragEnd} modifier={restrictToCalendar}>
      <UnscheduledContributions dt={dt} />
      <div className="wrapper">
        <div styleName="wrapper">
          <TimeGutter minHour={minHour} maxHour={maxHour} />
          <DnDCalendar>
            <div ref={calendarRef}>
              <Lines minHour={minHour} maxHour={maxHour} />
              <MemoizedTopLevelEntries dt={dt} entries={entries} />
              {newEntry && (
                <div style={{opacity: 0.5, pointerEvents: 'none'}}>
                  <DraggableEntry
                    id="draft"
                    width="100%"
                    title="New entry"
                    maxColumn={0}
                    {...newEntry}
                  />
                </div>
              )}
              {isModalOpen && newEntry && (
                <TimetableCreateModal
                  eventId={eventId}
                  onClose={() => {
                    setNewEntry(null);
                    setIsModalOpen(false);
                  }}
                  entry={newEntry}
                />
              )}
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
  const {y} = delta;
  const deltaMinutes = Math.ceil(pixelsToMinutes(y) / GRID_SIZE_MINUTES) * GRID_SIZE_MINUTES;
  const mousePosition = (mouse.x - over.rect.left) / over.rect.width;

  let fromEntry: Entry | undefined = entries.find(e => e.id === id);
  let fromBlock: BlockEntry | undefined;
  if (!fromEntry) {
    // If we didn't find the entry in the top level,
    // it must be a break inside a session block.
    fromBlock = entries
      .filter(e => e.type === 'block')
      .find(b => b.children.find(c => c.id === id));

    if (!fromBlock) {
      return;
    }

    fromEntry = fromBlock.children.find(c => c.id === id);
    if (!fromEntry || fromEntry.type !== 'break') {
      return;
    }
  }

  if (fromEntry.type === 'contrib' && fromEntry.sessionId) {
    return; // contributions with sessions assigned cannot be scheduled at the top level
  }

  const newEntry = {
    ...fromEntry,
    startDt: moment(fromEntry.startDt).add(deltaMinutes, 'minutes'),
    y: minutesToPixels(
      moment(fromEntry.startDt)
        .add(deltaMinutes, 'minutes')
        .diff(moment(fromEntry.startDt).startOf('day'), 'minutes')
    ),
  };

  if (isChildEntry(newEntry)) {
    delete newEntry.parentId;
  }

  if (newEntry.type === 'block') {
    newEntry.children = newEntry.children.map(e => ({
      ...e,
      startDt: moment(e.startDt).add(deltaMinutes, 'minutes'),
    }));
  }

  // Find all the entries that are linked to the new entry and recompute their layout
  const groupIds = getGroup(newEntry, entries.filter(e => e.id !== newEntry.id));
  let group = entries.filter(e => groupIds.has(e.id));
  group = layoutGroupAfterMove(group, newEntry, mousePosition);

  if (!fromBlock) {
    // Drop from top level to top level
    const oldGroupIds = getGroup(fromEntry, entries.filter(e => e.id !== fromEntry.id));
    let oldGroup = entries.filter(e => oldGroupIds.has(e.id) && !groupIds.has(e.id));
    const otherEntries = entries.filter(
      e => !groupIds.has(e.id) && !oldGroupIds.has(e.id) && e.id !== newEntry.id
    );
    oldGroup = layoutGroup(oldGroup, {layoutChildren: false});
    return [...otherEntries, ...oldGroup, ...group];
  } else {
    // Drop from block to top level (== a break)
    const otherEntries = entries.filter(
      e => !groupIds.has(e.id) && e.id !== newEntry.id && e.id !== fromBlock.id
    );
    if (groupIds.has(fromBlock.id)) {
      fromBlock = group.find(e => e.id === fromBlock.id);
      group = group.filter(e => e.id !== fromBlock.id);
    }
    fromBlock = {...fromBlock, children: fromBlock.children.filter(e => e.id !== newEntry.id)};
    fromBlock = {...fromBlock, children: layout(fromBlock.children)};
    // group = group.filter(e => e.id !== fromBlock.id); // might contain the block
    return [...otherEntries, ...group, fromBlock];
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

  const {y} = delta;
  const deltaMinutes = Math.ceil(pixelsToMinutes(y) / 5) * 5;
  const mousePosition = (mouse.x - over.rect.left) / over.rect.width;

  let fromEntry: Entry | undefined;
  if (!fromBlock) {
    fromEntry = entries.find(e => e.id === id);
    if (!fromEntry) {
      return;
    }
  } else {
    fromEntry = fromBlock.children.find(e => e.id === id);
  }

  if (!fromEntry) {
    return;
  }

  if (fromEntry.type === 'contrib') {
    if (!fromEntry.sessionId) {
      // Allow top level contributions being dropped on blocks to be treated as if they
      // were dropped directly on the calendar instead
      return layoutAfterDropOnCalendar(entries, who, calendar, delta, mouse);
    }
    if (fromEntry.sessionId !== toBlock.sessionId) {
      return; // contributions cannot be moved to blocks of different sessions
    }
  } else if (fromEntry.type === 'block') {
    // Allow blocks being dropped on other blocks to be treated as if they
    // were dropped directly on the calendar instead
    return layoutAfterDropOnCalendar(entries, who, calendar, delta, mouse);
  }

  if (fromEntry.duration > toBlock.duration) {
    return; // TODO: auto-resize the block?
  }

  const newEntry = {
    ...fromEntry,
    startDt: moment(fromEntry.startDt).add(deltaMinutes, 'minutes'),
    y: minutesToPixels(
      moment(fromEntry.startDt)
        .add(deltaMinutes, 'minutes')
        .diff(moment(toBlock.startDt), 'minutes')
    ),
    parentId: toBlock.id,
  };

  if (newEntry.startDt.isBefore(moment(toBlock.startDt))) {
    // move start time to the start of the block
    newEntry.startDt = moment(toBlock.startDt);
  } else if (
    moment(newEntry.startDt)
      .add(newEntry.duration, 'minutes')
      .isAfter(moment(toBlock.startDt).add(toBlock.duration, 'minutes'))
  ) {
    // move end time to the end of the block
    newEntry.startDt = moment(toBlock.startDt).add(toBlock.duration - newEntry.duration, 'minutes');
  }

  const groupIds = getGroup(newEntry, toBlock.children.filter(e => e.id !== newEntry.id));
  let group = toBlock.children.filter(e => groupIds.has(e.id));
  group = layoutGroupAfterMove(group, newEntry, mousePosition);

  const otherChildren = toBlock.children.filter(e => !groupIds.has(e.id) && e.id !== newEntry.id);

  if (!fromBlock) {
    return layout([
      ...entries.filter(e => e.id !== newEntry.id && e.id !== toBlock.id),
      {...toBlock, children: [...otherChildren, ...group]},
    ]);
  } else if (toBlock.id === fromBlock.id) {
    const otherEntries = entries.filter(e => e.id !== toBlock.id);
    return layout([...otherEntries, {...toBlock, children: [...otherChildren, ...group]}]);
  } else {
    const otherEntries = entries.filter(e => e.id !== toBlock.id && e.id !== fromBlock.id);
    const fromChildren = fromBlock.children.filter(e => e.id !== newEntry.id);
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
  who: string,
  calendar: Over,
  delta: Transform,
  mouse: MousePosition,
  offset
) {
  const id = parseInt(who.slice('unscheduled-'.length), 10);
  const deltaMinutes = 0;
  const mousePositionX = (mouse.x - calendar.rect.left) / calendar.rect.width;
  const mousePositionY = mouse.y - calendar.rect.top - window.scrollY;
  const startDt = moment(dt)
    .startOf('day')
    .add(snapMinutes(pixelsToMinutes(mousePositionY - offset.y)), 'minutes');

  let entry = unscheduled.find(e => e.id === id);
  if (!entry) {
    return;
  }

  if (entry.type !== 'contrib') {
    return;
  }

  if (entry.sessionId) {
    return;
  }

  entry = {
    ...entry,
    startDt,
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

function layoutAfterUnscheduledDropOnBlock(
  dt: Moment,
  unscheduled: TopLevelEntry[],
  entries: TopLevelEntry[],
  who: string,
  over: Over,
  delta: Transform,
  mouse: MousePosition,
  offset,
  calendar: Over
) {
  const id = parseInt(who.slice('unscheduled-'.length), 10);
  const overId = parseInt(over.id, 10);
  const toBlock = entries.find(e => e.id === overId);
  if (toBlock.type !== 'block') {
    return;
  }
  const deltaMinutes = 0;
  const mousePositionX = (mouse.x - over.rect.left) / over.rect.width;
  const mousePositionY = mouse.y - calendar.rect.top - window.scrollY;

  const startDt = moment(dt)
    .startOf('day')
    .add(snapMinutes(pixelsToMinutes(mousePositionY - offset.y)), 'minutes');

  const entry = unscheduled.find(e => e.id === id);
  if (!entry) {
    return;
  }

  if (entry.type !== 'contrib') {
    return;
  }

  if (entry.sessionId !== toBlock.sessionId) {
    if (!entry.sessionId) {
      return layoutAfterUnscheduledDrop(
        dt,
        unscheduled,
        entries,
        who,
        calendar,
        delta,
        mouse,
        offset
      );
    }
    return;
  }

  if (entry.duration > toBlock.duration) {
    return; // TODO: auto-resize the block?
  }

  const newEntry = {
    ...entry,
    startDt,
    y: minutesToPixels(
      moment(startDt)
        .add(deltaMinutes, 'minutes')
        .diff(moment(toBlock.startDt), 'minutes')
    ),
    parentId: toBlock.id,
  };

  // TODO
  if (newEntry.backgroundColor) {
    delete newEntry.backgroundColor;
  }

  if (newEntry.startDt.isBefore(moment(toBlock.startDt))) {
    // move start time to the start of the block
    newEntry.startDt = moment(toBlock.startDt);
  } else if (
    moment(newEntry.startDt)
      .add(newEntry.duration, 'minutes')
      .isAfter(moment(toBlock.startDt).add(toBlock.duration, 'minutes'))
  ) {
    // move end time to the end of the block
    newEntry.startDt = moment(toBlock.startDt).add(toBlock.duration - newEntry.duration, 'minutes');
  }

  const groupIds = getGroup(newEntry, toBlock.children.filter(e => e.id !== newEntry.id));
  let group = toBlock.children.filter(e => groupIds.has(e.id));
  group = layoutGroupAfterMove(group, newEntry, mousePositionX);

  const otherChildren = toBlock.children.filter(e => !groupIds.has(e.id) && e.id !== newEntry.id);

  return [
    layout([
      ...entries.filter(e => e.id !== newEntry.id && e.id !== toBlock.id),
      {...toBlock, children: [...otherChildren, ...group]},
    ]),
    unscheduled.filter(e => e.id !== id),
  ];
}
