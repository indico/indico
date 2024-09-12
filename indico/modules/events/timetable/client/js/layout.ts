import moment, {Moment} from 'moment';

import {Entry, TopLevelEntry, DayEntries} from './types.ts';
import {lcm, minutesToPixels} from './utils.ts';

function overlap<T extends Entry>(a: T, b: T) {
  const aEnd = a.startDt.clone().add(a.duration, 'minutes');
  const bEnd = b.startDt.clone().add(b.duration, 'minutes');
  return a.startDt.isBefore(bEnd) && b.startDt.isBefore(aEnd);
}

export function layoutDays(dayEntries: DayEntries): DayEntries {
  return Object.fromEntries(
    Object.entries(dayEntries).map(([day, entries]) => [day, layout(entries)])
  );
}

export function layout<T extends Entry>(entries: T[]) {
  const groups = getGroups(entries);
  let newEntries: T[] = [];
  for (const group of groups) {
    const groupEntries = entries.filter(entry => group.has(entry.id));
    newEntries = [...newEntries, ...layoutGroup(groupEntries)];
  }
  return newEntries;
}

export function layoutGroup<T extends Entry>(group: T[]) {
  group = group.map(entry =>
    entry.type === 'block' ? {...entry, children: layout(entry.children)} : entry
  );
  const sortedGroup = [...group].sort((a, b) => a.column - b.column);
  const newGroup: T[] = [];
  for (const entry of sortedGroup) {
    const overlappingEntries = newGroup.filter(e => overlap(e, entry));
    const maxColumn = Math.max(...overlappingEntries.map(e => e.column), 0);
    const newColumn = overlappingEntries.length === 0 ? 0 : maxColumn + 1;
    newGroup.push({
      ...entry,
      column: newColumn,
    });
  }
  const maxColumn = getMaximumParallelEntries(newGroup);
  const columnWidth = 100 / (maxColumn + 1);
  return newGroup.map(entry => ({
    ...entry,
    width: `${columnWidth}%`,
    x: `${entry.column * columnWidth}%`,
    maxColumn,
  }));
}

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

  newEntry = {
    ...newEntry,
    column: ((newEntry.column + 1) * newColumnCount) / (1 + newEntry.maxColumn) - 1,
    maxColumn: newColumnCount,
  };

  const selectedColumn = Math.floor(newColumnCount * mousePosition);

  const rightToLeft = selectedColumn < newEntry.column;
  if (selectedColumn === 0) {
    group = group.map(entry => ({
      ...entry,
      column: entry.column + 1,
    }));
  } else if (selectedColumn === newColumnCount - 1) {
    // TODO
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

  const sortedGroup = [...group].sort((a, b) => a.column - b.column);
  const newGroup: T[] = [];
  for (const entry of sortedGroup) {
    const overlappingEntries = newGroup.filter(e => overlap(e, entry));
    const maxColumn = Math.max(...overlappingEntries.map(e => e.column), 0);
    const newColumn = overlappingEntries.length === 0 ? 0 : maxColumn + 1;
    newGroup.push({
      ...entry,
      column: newColumn,
    });
  }
  const maxColumn = getMaximumParallelEntries(newGroup);
  const columnWidth = 100 / (maxColumn + 1);
  return newGroup.map(entry => ({
    ...entry,
    width: `${columnWidth}%`,
    x: `${entry.column * columnWidth}%`,
    maxColumn,
  }));
}

export function getGroups(entries: TopLevelEntry[]) {
  const groups: Set<number>[] = [];
  const seen = new Set<number>();

  for (const entry of entries) {
    if (seen.has(entry.id)) {
      continue;
    }

    const group = new Set<number>();
    group.add(entry.id);
    seen.add(entry.id);
    dfs(entry, entries, group, seen);
    groups.push(group);
  }

  return groups;
}

export function getGroup(entry: TopLevelEntry, entries: TopLevelEntry[]) {
  const group = new Set<number>();
  const seen = new Set<number>();
  seen.add(entry.id);
  dfs(entry, entries, group, seen);
  return group;
}

function dfs(curr: Entry, entries: TopLevelEntry[], group: Set<number>, seen: Set<number>) {
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

function getMaximumParallelEntries(entries: TopLevelEntry[]) {
  return Math.max(...entries.map(entry => entry.column), 0);
}

export function getParallelEntries(entry: TopLevelEntry, entries: TopLevelEntry[]) {
  return entries.filter(e => overlap(e, entry));
}

export function computeYoffset(entries: TopLevelEntry[], startHour: number): TopLevelEntry[] {
  return entries.map(entry => {
    const offsetMinutes = moment(entry.startDt).diff(
      moment(entry.startDt)
        .startOf('day')
        .add(startHour, 'hours'),
      'minutes'
    );
    if (entry.type !== 'block') {
      return {...entry, y: minutesToPixels(offsetMinutes)};
    }
    const children = entry.children.map(child => ({
      ...child,
      y: minutesToPixels(moment(child.startDt).diff(entry.startDt, 'minutes')),
    }));
    return {...entry, y: minutesToPixels(offsetMinutes), children};
  });
}
