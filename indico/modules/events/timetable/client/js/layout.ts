// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';

import {Transform, Over, MousePosition} from './dnd';
import {TopLevelEntry, Entry, EntryType, DayEntries} from './types';
import {lcm, minutesToPixels, pixelsToMinutes, snapMinutes} from './utils.ts';

function overlap<T extends Entry>(a: T, b: T) {
  const aEnd = a.startDt.clone().add(Math.max(a.duration, 10), 'minutes');
  const bEnd = b.startDt.clone().add(Math.max(b.duration, 10), 'minutes');
  return a.startDt.isBefore(bEnd) && b.startDt.isBefore(aEnd);
}

/**
 * Recompute the layout of multiple days
 */
export function layoutDays(dayEntries: DayEntries): DayEntries {
  return Object.fromEntries(
    Object.entries(dayEntries).map(([day, entries]) => [day, layout(entries)])
  );
}

/**
 * Recompute the layout of a list of entries.
 * These can be either top-level entries or child entries.
 */
export function layout<T extends Entry>(entries: T[]) {
  const groups = getGroups(entries);
  let newEntries: T[] = [];
  for (const group of groups) {
    const groupEntries = entries.filter(entry => group.has(entry.id));
    newEntries = [...newEntries, ...layoutGroup(groupEntries)];
  }
  return newEntries;
}

/**
 * Recompute the layout of a group of entries. A group is a set of entries
 * that all overlap with each other either directly or transitively via some
 * other common entry.
 *
 * This function can be used either for the initial layout (even if the entries don't have
 * .column set) or to recompute the layout after removing an entry from the group.
 * The function takes care of removing any 'holes' in the layout.
 * */
export function layoutGroup<T extends Entry>(group: T[], {layoutChildren = true} = {}) {
  if (layoutChildren) {
    group = group.map(entry =>
      entry.type === 'block' ? {...entry, children: layout(entry.children)} : entry
    );
  }

  const sortedGroup = [...group].sort((a, b) => a.column - b.column); // TODO: secondary sort by duration(DESC)
  const newGroup: T[] = [];
  let newMaxColumn = 0;
  for (const entry of sortedGroup) {
    const overlappingEntries = newGroup.filter(e => overlap(e, entry));
    const maxColumn = Math.max(...overlappingEntries.map(e => e.column), 0);
    const newColumn = overlappingEntries.length === 0 ? 0 : maxColumn + 1;
    newMaxColumn = Math.max(newMaxColumn, newColumn);
    newGroup.push({
      ...entry,
      column: newColumn,
    });
  }
  return newGroup.map(entry => ({
    ...entry,
    maxColumn: newMaxColumn,
  }));
}

/**
 * Similar to layoutGroup, but used after a new entry was
 * added to the group. Based on the mouse position, the new entry
 * is placed in a corresponding column and the existing entries are shifted
 * to the left or right to make space for it.
 */
export function layoutGroupAfterMove<T extends Entry>(
  group: T[],
  newEntry: T,
  mousePosition: number
) {
  const columnCounts = new Set(group.map(entry => entry.maxColumn + 1));
  const newColumnCount = lcm(...columnCounts);
  group = group.map(entry => ({
    ...entry,
    column: ((entry.column + 1) * newColumnCount) / (1 + entry.maxColumn) - 1,
    maxColumn: newColumnCount,
  }));

  const selectedColumn = Math.floor(newColumnCount * mousePosition);
  const isUnscheduled = !Number.isInteger(newEntry.column);
  newEntry = {
    ...newEntry,
    column: isUnscheduled
      ? selectedColumn
      : ((newEntry.column + 1) * newColumnCount) / (1 + newEntry.maxColumn) - 1,
    maxColumn: newColumnCount,
  };

  const rightToLeft = selectedColumn < newEntry.column;
  if (newColumnCount === 1) {
    if (mousePosition <= 0.5) {
      group = group.map(entry => ({
        ...entry,
        column: entry.column + 1,
      }));
      return layoutGroup([...group, newEntry]);
    } else {
      newEntry = {
        ...newEntry,
        column: 1,
        maxColumn: newColumnCount,
      };
      return layoutGroup([...group, newEntry]);
    }
  } else if (selectedColumn === 0) {
    group = group.map(entry => ({
      ...entry,
      column: entry.column + 1,
    }));
  } else if (selectedColumn === newColumnCount - 1) {
    newEntry = {
      ...newEntry,
      column: newEntry.column + 1,
    };
  } else if (rightToLeft) {
    group = group.map(entry => ({
      ...entry,
      column: entry.column < selectedColumn ? entry.column : entry.column + 1,
    }));
  } else {
    group = group.map(entry => ({
      ...entry,
      column: entry.column <= selectedColumn ? entry.column : entry.column + 1,
    }));
  }

  group = [
    ...group,
    {
      ...newEntry,
      column: rightToLeft ? selectedColumn : selectedColumn + 1,
      maxColumn: newColumnCount,
    },
  ];

  return layoutGroup(group);
}

/**
 * Finds all groups of overlapping entries.
 * You can think of this as finding all connected components in a graph.
 * See getGroup for more details on what a 'group' is.
 */
export function getGroups(entries: TopLevelEntry[]) {
  const groups: Set<string>[] = [];
  const seen = new Set<string>();

  for (const entry of entries) {
    if (seen.has(entry.id)) {
      continue;
    }

    const group = new Set<string>();
    group.add(entry.id);
    seen.add(entry.id);
    dfs(entry, entries, group, seen);
    groups.push(group);
  }

  return groups;
}

/**
 * Finds all entries that overlap (either directly via another entry) with the
 * given entry.
 *
 * For example, for entries A (8-10), B (10-12) and C (9:11) the group of A would
 * be {B, C}. because B is 'reachable' from A via C.
 */
export function getGroup(entry: TopLevelEntry, entries: TopLevelEntry[]) {
  const group = new Set<string>();
  const seen = new Set<string>();
  seen.add(entry.id);
  dfs(entry, entries, group, seen);
  return group;
}

function dfs(curr: Entry, entries: TopLevelEntry[], group: Set<string>, seen: Set<string>) {
  for (const entry of entries) {
    if (seen.has(entry.id)) {
      continue;
    }

    if (overlap(curr, entry)) {
      seen.add(entry.id);
      group.add(entry.id);
      dfs(entry, entries, group, seen);
    }
  }
}

export function getParallelEntries(entry: TopLevelEntry, entries: TopLevelEntry[]) {
  return entries.filter(e => overlap(e, entry));
}

export function computeYoffset(entries: TopLevelEntry[], startHour: number): TopLevelEntry[] {
  return entries.map(entry => {
    const offsetMinutes = moment(entry.startDt).diff(
      moment(entry.startDt).startOf('day').add(startHour, 'hours'),
      'minutes'
    );
    if (entry.type !== 'block') {
      return {...entry, y: minutesToPixels(offsetMinutes)};
    }
    const children = entry.children.map(child => ({
      // TODO: no need to compute y offset for children here
      ...child,
      y: minutesToPixels(moment(child.startDt).diff(entry.startDt, 'minutes')),
    }));
    return {...entry, y: minutesToPixels(offsetMinutes), children};
  });
}

/**
 * The column and maxColumn property of an entry determines
 * the width and horizontal position in the timetable (or in a block).
 *
 * For example for 4 overlapping entries the column property
 * the width and offset would be:
 *
 * A: {column: 0, maxColumn: 3} -> {width: 25%, offset:  0%}
 * B: {column: 1, maxColumn: 3} -> {width: 25%, offset: 25%}
 * C: {column: 2, maxColumn: 3} -> {width: 25%, offset: 50%}
 * D: {column: 3, maxColumn: 3} -> {width: 25%, offset: 75%}
 */
export function getWidthAndOffset(column, maxColumn) {
  const columnWidth = 100 / (maxColumn + 1);
  return {
    width: `${columnWidth}%`,
    offset: `${column * columnWidth}%`,
  };
}

export function layoutAfterUnscheduledDrop(
  dt: Moment,
  unscheduled: TopLevelEntry[],
  entries: TopLevelEntry[],
  who: string,
  calendar: Over,
  delta: Transform,
  mouse: MousePosition,
  offset: MousePosition
) {
  const id = who.slice('unscheduled-'.length);
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

  if (entry.type !== EntryType.Contribution) {
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
  return [layout([...otherEntries, ...group]), unscheduled.filter(e => e.id !== id), startDt];
}

export function layoutAfterUnscheduledDropOnBlock(
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
  const id = who.slice('unscheduled-'.length);
  const overId = over.id;
  const toBlock = entries.find(e => e.id === overId);
  if (toBlock.type !== EntryType.SessionBlock) {
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

  if (entry.type !== EntryType.Contribution) {
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

  const draftEntry = {
    ...entry,
    startDt,
    y: minutesToPixels(
      moment(startDt).add(deltaMinutes, 'minutes').diff(moment(toBlock.startDt), 'minutes')
    ),
    sessionBlockId: toBlock.id,
  };

  // TODO
  if (draftEntry.backgroundColor) {
    delete draftEntry.backgroundColor;
  }

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

  const groupIds = getGroup(
    draftEntry,
    toBlock.children.filter(e => e.id !== draftEntry.id)
  );
  let group = toBlock.children.filter(e => groupIds.has(e.id));
  group = layoutGroupAfterMove(group, draftEntry, mousePositionX);

  const otherChildren = toBlock.children.filter(e => !groupIds.has(e.id) && e.id !== draftEntry.id);

  return [
    layout([
      ...entries.filter(e => e.id !== draftEntry.id && e.id !== toBlock.id),
      {...toBlock, children: [...otherChildren, ...group]},
    ]),
    unscheduled.filter(e => e.id !== id),
    startDt,
    toBlock.objId,
  ];
}
