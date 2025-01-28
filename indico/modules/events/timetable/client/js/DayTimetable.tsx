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
import {ContributionCreateForm} from '../../../contributions/client/js/ContributionForm';

import * as actions from './actions';
import {createRestrictToElement, Transform, Over, MousePosition} from './dnd';
import {useDroppable, DnDProvider} from './dnd/dnd';
import {DraggableBlockEntry, DraggableEntry} from './Entry';
import {computeYoffset, getGroup, layout, layoutGroup, layoutGroupAfterMove} from './layout';
import * as selectors from './selectors';
import {TopLevelEntry, BlockEntry, Entry, isChildEntry, BaseEntry} from './types';
import UnscheduledContributions from './UnscheduledContributions';
import {minutesToPixels, pixelsToMinutes} from './utils';

// TODO: (Ajob) Remove when discussed how to handle pre-existing uniqueID type
type UniqueId = string;

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

  const [blockModal, setOpenBlockModal] = useState<ContributionCreateForm | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [newEntry, setNewEntry] = useState<BaseEntry | null>(null);

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

  useEffect(() => {
    function onCloseModal() {
      setOpenBlockModal(null);
      setNewEntry(null);
    }

    function handler() {
      setOpenBlockModal(
        <ContributionCreateForm
          eventId={5}
          onClose={onCloseModal}
          customFields={[
            {
              id: 'fields_test',
              fieldType: 'text',
              title: 'test',
              description: 'Field for testing',
              isRequired: false,
              fieldData: {},
            },
          ]}
          customInitialValues={{duration: 50000}}
        />
      );
    }

    calendarRef.current.addEventListener('click', handler);

    return () => {
      calendarRef.current.removeEventListener('click', handler);
    };
  }, [blockModal]);

  useEffect(() => {
    function onMouseDown(event: MouseEvent) {
      // TODO: (Ajob) uncomment this after checking why this is invalid all the time
      // if (event.target !== calendarRef.current) {
      //   return;
      // }
      setIsDragging(true);
      const rect = calendarRef.current.getBoundingClientRect();
      const minuteStepSize = 5;
      const y = Math.floor((event.clientY - rect.top) / minuteStepSize) * minuteStepSize;
      const startDt = moment(dt)
        .startOf('day')
        .add(y, 'minutes');

      setNewEntry({
        id: -1,
        type: 'contrib',
        startDt,
        duration: 0,
        x: 0,
        y,
        title: 'New entry',
        width: '100%',
        column: 0,
        maxColumn: 0,
      });
    }

    function onMouseMove(event: MouseEvent) {
      if (!isDragging || !newEntry) {
        return;
      }
      const rect = calendarRef.current.getBoundingClientRect();
      const y = event.clientY - rect.top;
      const duration =
        pixelsToMinutes(y) -
        pixelsToMinutes(newEntry.startDt.diff(moment(dt).startOf('day'), 'minutes'));

      const newDuration = Math.max(Math.floor(duration / 5) * 5, 5);
      if (duration === newDuration) {
        return;
      }
      setNewEntry({...newEntry, duration: newDuration});
    }

    function onMouseUp() {
      if (isDragging && newEntry) {
        // TODO: (Ajob) Move to actual place to create and uncomment once implemented
        // dispatch(actions.createEntry(newEntry));
        setIsDragging(false);
        setNewEntry(null);
      }
    }

    calendarRef.current.addEventListener('mousedown', onMouseDown);
    calendarRef.current.addEventListener('mousemove', onMouseMove);
    calendarRef.current.addEventListener('mouseup', onMouseUp);

    return () => {
      calendarRef.current.removeEventListener('mousedown', onMouseDown);
      calendarRef.current.removeEventListener('mousemove', onMouseMove);
      calendarRef.current.removeEventListener('mouseup', onMouseUp);
    };
  }, [isDragging, newEntry, dt, dispatch]);

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
              {newEntry && (
                <div style={{opacity: 0.5}}>
                  <MemoizedTopLevelEntries dt={dt} entries={[newEntry]} />
                </div>
              )}
              {blockModal}
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
  const deltaMinutes = Math.ceil(pixelsToMinutes(y) / 5) * 5;
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
