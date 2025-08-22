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
import {
  computeYoffset,
  getGroup,
  layout,
  layoutGroup,
  layoutGroupAfterMove,
  layoutAfterUnscheduledDrop,
  layoutAfterUnscheduledDropOnBlock,
} from './layout';
import * as selectors from './selectors';
import TimetableManageModal from './TimetableManageModal';
import {TopLevelEntry, BlockEntry, Entry, isChildEntry, EntryType} from './types';
import UnscheduledContributions from './UnscheduledContributions';
import {GRID_SIZE_MINUTES, minutesToPixels, pixelsToMinutes} from './utils';

interface DayTimetableProps {
  dt: Moment;
  eventId: number;
  minHour: number;
  maxHour: number;
  entries: TopLevelEntry[];
}

function TopLevelEntries({dt, entries}: {dt: Moment; entries: TopLevelEntry[]}) {
  const dispatch = useDispatch();

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
      obj[e.id] = (id: string) => (duration: number) =>
        dispatch(actions.resizeEntry(dt.format('YYYYMMDD'), id, duration, e.id));
    }
    return obj;
  }, [entries, dispatch, dt]);

  return (
    <>
      {entries.map(entry =>
        entry.type === EntryType.SessionBlock ? (
          <DraggableBlockEntry
            key={entry.id}
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

  const [isDragging, setIsDragging] = useState(false);

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
        return handleUnscheduledDrop(who, calendar, delta, mouse, offset);
      } else {
        const block = over.find(o => o.id !== 'calendar');
        if (block) {
          return handleUnscheduledDropOnBlock(who, block, delta, mouse, offset, calendar);
        }
      }
    }

    const calendar = over.find(o => o.id === 'calendar');
    if (!calendar) {
      return;
    }

    if (over.length === 1) {
      return handleDropOnCalendar(who, calendar, delta, mouse);
    } else {
      const block = over.find(o => o.id !== 'calendar');
      if (block) {
        return handleDropOnBlock(who, block, delta, mouse, calendar);
      }
    }
  }

  function handleUnscheduledDrop(
    who: string,
    over: Over,
    delta: Transform,
    mouse: MousePosition,
    offset
  ) {
    const [newLayout, newUnscheduled, startDt] =
      layoutAfterUnscheduledDrop(dt, unscheduled, entries, who, over, delta, mouse, offset) || [];
    if (!newLayout) {
      return;
    }
    // TODO(tomas): use something better than 'unscheduled-' prefix
    const contribId = parseInt(who.slice('unscheduled-c'.length), 10);
    dispatch(actions.scheduleEntry(eventId, contribId, startDt, newLayout, newUnscheduled));
  }

  function handleUnscheduledDropOnBlock(
    who: string,
    over: Over,
    delta: Transform,
    mouse: MousePosition,
    offset,
    calendar: Over
  ) {
    const [newLayout, newUnscheduled, startDt, blockId] =
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
    // TODO(tomas): use something better than 'unscheduled-' prefix
    const contribId = parseInt(who.slice('unscheduled-c'.length), 10);
    dispatch(
      actions.scheduleEntry(eventId, contribId, startDt, newLayout, newUnscheduled, blockId)
    );
  }

  function handleDropOnCalendar(who: string, over: Over, delta: Transform, mouse: MousePosition) {
    const [newLayout, movedEntry] = layoutAfterDropOnCalendar(entries, who, over, delta, mouse);
    dispatch(actions.moveEntry(movedEntry, eventId, newLayout, dt.format('YYYYMMDD')));
  }

  function handleDropOnBlock(
    who: string,
    over: Over,
    delta: Transform,
    mouse: MousePosition,
    calendar: Over
  ) {
    const [newLayout, movedEntry] = layoutAfterDropOnBlock(
      entries,
      who,
      over,
      delta,
      mouse,
      calendar
    );
    dispatch(actions.moveEntry(movedEntry, eventId, newLayout, dt.format('YYYYMMDD')));
  }

  const draftEntry = useSelector(selectors.getDraftEntry);

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
    function onMouseDown(event: MouseEvent) {
      if (event.button !== 0 || event.target !== calendarRef.current) {
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
      dispatch(
        actions.setDraftEntry({
          startDt,
          duration: GRID_SIZE_MINUTES, // TODO: (Ajob) Replace with default duration
          y,
        })
      );
    }

    function onMouseMove(event: MouseEvent) {
      if (!isDragging || !draftEntry) {
        return;
      }
      const rect = calendarRef.current.getBoundingClientRect();
      const duration = Math.max(
        Math.round(pixelsToMinutes(event.clientY - rect.top - draftEntry.y) / GRID_SIZE_MINUTES) *
          GRID_SIZE_MINUTES,
        GRID_SIZE_MINUTES // TODO: Replace with default duration
      );

      if (draftEntry.duration === duration) {
        return;
      }

      dispatch(actions.setDraftEntry({...draftEntry, duration}));
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsDragging(false);
        dispatch(actions.setDraftEntry(null));
      }
    }

    function onMouseUp() {
      if (isDragging && draftEntry) {
        setIsDragging(false);
      }
    }

    const calendar = calendarRef.current;
    calendar.addEventListener('mousedown', onMouseDown);
    calendar.addEventListener('mousemove', onMouseMove);
    calendar.addEventListener('mouseup', onMouseUp);
    document.addEventListener('keydown', onKeyDown);

    return () => {
      calendar.removeEventListener('mousedown', onMouseDown);
      calendar.removeEventListener('mousemove', onMouseMove);
      calendar.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [draftEntry, dt, dispatch, isDragging, minHour]);

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
              {draftEntry && (
                <div style={{opacity: 0.5, pointerEvents: 'none'}}>
                  <DraggableEntry
                    id="draft"
                    width="100%"
                    title="New entry"
                    maxColumn={0}
                    {...draftEntry}
                  />
                </div>
              )}
              {!isDragging && draftEntry && (
                <TimetableManageModal
                  eventId={eventId}
                  onClose={() => {
                    dispatch(actions.setDraftEntry(null));
                  }}
                  entry={draftEntry}
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
  first?: boolean;
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
  who: string,
  over: Over,
  delta: Transform,
  mouse: MousePosition
) {
  const {y} = delta;
  const deltaMinutes = Math.ceil(pixelsToMinutes(y) / GRID_SIZE_MINUTES) * GRID_SIZE_MINUTES;
  const mousePosition = (mouse.x - over.rect.left) / over.rect.width;

  let fromEntry: Entry | undefined = entries.find(e => e.id === who);
  let fromBlock: BlockEntry | undefined;
  if (!fromEntry) {
    // If we didn't find the entry in the top level,
    // it must be a break inside a session block.
    fromBlock = entries
      .filter(e => e.type === EntryType.SessionBlock)
      .find(b => b.children.find(c => c.id === who));

    if (!fromBlock) {
      return;
    }

    fromEntry = fromBlock.children.find(c => c.id === who);
    if (!fromEntry || fromEntry.type !== EntryType.Break) {
      return;
    }
  }

  if (fromEntry.type === EntryType.Contribution && fromEntry.sessionId) {
    return; // contributions with sessions assigned cannot be scheduled at the top level
  }

  const draftEntry = {
    ...fromEntry,
    startDt: moment(fromEntry.startDt).add(deltaMinutes, 'minutes'),
    y: minutesToPixels(
      moment(fromEntry.startDt)
        .add(deltaMinutes, 'minutes')
        .diff(moment(fromEntry.startDt).startOf('day'), 'minutes')
    ),
  };

  if (isChildEntry(draftEntry)) {
    delete draftEntry.parentId;
  }

  if (draftEntry.type === EntryType.SessionBlock) {
    draftEntry.children = draftEntry.children.map(e => ({
      ...e,
      startDt: moment(e.startDt).add(deltaMinutes, 'minutes'),
    }));
  }

  // Find all the entries that are linked to the new entry and recompute their layout
  const groupIds = getGroup(draftEntry, entries.filter(e => e.id !== draftEntry.id));
  let group = entries.filter(e => groupIds.has(e.id));
  group = layoutGroupAfterMove(group, draftEntry, mousePosition);

  if (!fromBlock) {
    // Drop from top level to top level
    const oldGroupIds = getGroup(fromEntry, entries.filter(e => e.id !== fromEntry.id));
    let oldGroup = entries.filter(e => oldGroupIds.has(e.id) && !groupIds.has(e.id));
    const otherEntries = entries.filter(
      e => !groupIds.has(e.id) && !oldGroupIds.has(e.id) && e.id !== draftEntry.id
    );
    oldGroup = layoutGroup(oldGroup, {layoutChildren: false});
    return [[...otherEntries, ...oldGroup, ...group], draftEntry];
  } else {
    // Drop from block to top level (== a break)
    const otherEntries = entries.filter(
      e => !groupIds.has(e.id) && e.id !== draftEntry.id && e.id !== fromBlock.id
    );
    if (groupIds.has(fromBlock.id)) {
      fromBlock = group.find(e => e.id === fromBlock.id);
      group = group.filter(e => e.id !== fromBlock.id);
    }
    fromBlock = {...fromBlock, children: fromBlock.children.filter(e => e.id !== draftEntry.id)};
    fromBlock = {...fromBlock, children: layout(fromBlock.children)};
    // group = group.filter(e => e.id !== fromBlock.id); // might contain the block
    return [[...otherEntries, ...group, fromBlock], draftEntry];
  }
}

function layoutAfterDropOnBlock(
  entries: TopLevelEntry[],
  who: string,
  over: Over,
  delta: Transform,
  mouse: MousePosition,
  calendar: Over
) {
  const overId = over.id;
  const toBlock = entries.find(e => e.id === overId);

  if (!toBlock || toBlock.type !== EntryType.SessionBlock) {
    return;
  }

  const fromBlock = entries
    .filter(e => e.type === EntryType.SessionBlock)
    .find(entry => !!entry.children.find(c => c.id === who));

  const {y} = delta;
  const deltaMinutes = Math.ceil(pixelsToMinutes(y) / 5) * 5;
  const mousePosition = (mouse.x - over.rect.left) / over.rect.width;

  let fromEntry: Entry | undefined;
  if (!fromBlock) {
    fromEntry = entries.find(e => e.id === who);
    if (!fromEntry) {
      return;
    }
  } else {
    fromEntry = fromBlock.children.find(e => e.id === who);
  }

  if (!fromEntry) {
    return;
  }

  if (fromEntry.type === EntryType.Contribution) {
    if (!fromEntry.sessionId) {
      // Allow top level contributions being dropped on blocks to be treated as if they
      // were dropped directly on the calendar instead
      return layoutAfterDropOnCalendar(entries, who, calendar, delta, mouse);
    }
    if (fromEntry.sessionId !== toBlock.sessionId) {
      return; // contributions cannot be moved to blocks of different sessions
    }
  } else if (fromEntry.type === EntryType.SessionBlock) {
    // Allow blocks being dropped on other blocks to be treated as if they
    // were dropped directly on the calendar instead
    return layoutAfterDropOnCalendar(entries, who, calendar, delta, mouse);
  }

  if (fromEntry.duration > toBlock.duration) {
    return; // TODO: auto-resize the block?
  }

  const draftEntry = {
    ...fromEntry,
    startDt: moment(fromEntry.startDt).add(deltaMinutes, 'minutes'),
    y: minutesToPixels(
      moment(fromEntry.startDt)
        .add(deltaMinutes, 'minutes')
        .diff(moment(toBlock.startDt), 'minutes')
    ),
    parentId: toBlock.id,
  };

  if (draftEntry.startDt.isBefore(moment(toBlock.startDt))) {
    // move start time to the start of the block
    draftEntry.startDt = moment(toBlock.startDt);
  } else if (
    moment(draftEntry.startDt)
      .add(draftEntry.duration, 'minutes')
      .isAfter(moment(toBlock.startDt).add(toBlock.duration, 'minutes'))
  ) {
    // move end time to the end of the block
    draftEntry.startDt = moment(toBlock.startDt).add(
      toBlock.duration - draftEntry.duration,
      'minutes'
    );
  }

  const groupIds = getGroup(draftEntry, toBlock.children.filter(e => e.id !== draftEntry.id));
  let group = toBlock.children.filter(e => groupIds.has(e.id));
  group = layoutGroupAfterMove(group, draftEntry, mousePosition);

  const otherChildren = toBlock.children.filter(e => !groupIds.has(e.id) && e.id !== draftEntry.id);

  if (!fromBlock) {
    return [
      layout([
        ...entries.filter(e => e.id !== draftEntry.id && e.id !== toBlock.id),
        {...toBlock, children: [...otherChildren, ...group]},
      ]),
      draftEntry,
    ];
  } else if (toBlock.id === fromBlock.id) {
    const otherEntries = entries.filter(e => e.id !== toBlock.id);
    return [
      layout([...otherEntries, {...toBlock, children: [...otherChildren, ...group]}]),
      draftEntry,
    ];
  } else {
    const otherEntries = entries.filter(e => e.id !== toBlock.id && e.id !== fromBlock.id);
    const fromChildren = fromBlock.children.filter(e => e.id !== draftEntry.id);
    return [
      layout([
        ...otherEntries,
        {...fromBlock, children: fromChildren},
        {...toBlock, children: [...otherChildren, ...group]},
      ]),
      draftEntry,
    ];
  }
}
