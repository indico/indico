// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

// TODO: remove second condition when we start using number ids
export const hasParent = entry => _.isNumber(entry.parent) || entry.parent;

export const hasChild = (entry, entries) => entries.some(e => e.parent === entry.id);

export const getConcurrentEntries = (entry, entries) =>
  entries.filter(e => e.id !== entry.id && e.start < entry.end && e.end > entry.start);

const getColumnId = (entry, topLevelEntries, draggedEntry) => {
  if (hasParent(entry)) {
    if (draggedEntry?.entryId === entry.id) {
      return draggedEntry.targetResourceId;
    }
    return getColumnId(
      topLevelEntries.find(e => e.id === entry.parent),
      topLevelEntries,
      draggedEntry
    );
  }
  // find all concurrent entries
  const concurrent = getConcurrentEntries(entry, topLevelEntries);
  if (concurrent.length === 0) {
    return 1;
  }
  // if this is the first time we're assigning a resource id, we need check the desired display order
  if (!draggedEntry) {
    const [orderedConcurrent, unorderedConcurrent] = _.partition([...concurrent, entry], e =>
      _.isNumber(e.displayOrder)
    );
    return _.isNumber(entry.displayOrder)
      ? _.sortBy(orderedConcurrent, 'displayOrder').findIndex(e => e.id === entry.id) + 1
      : _.sortBy(unorderedConcurrent, ['code', 'title']).findIndex(e => e.id === entry.id) +
          orderedConcurrent.length +
          1;
  }
  // if this is the dragged entry, assign it its targeted resource id
  if (draggedEntry.entryId === entry.id) {
    return draggedEntry.targetResourceId;
  }
  const wasPushedRight = e => {
    const c = e.id === entry.id ? concurrent : getConcurrentEntries(e, topLevelEntries);
    return (
      draggedEntry.entryId !== e.id &&
      draggedEntry.targetResourceId === e.resourceId &&
      draggedEntry.sourceResourceId >= draggedEntry.targetResourceId &&
      c.some(ev => ev.id === draggedEntry.entryId || e.resourceId === draggedEntry.sourceResourceId)
    );
  };
  // if moving to the left and the spot is occupied, move it one to the right
  if (wasPushedRight(entry)) {
    return draggedEntry.targetResourceId + 1;
  }
  // if this entry is concurrent with the dragged entry and is in the same resource, we need to
  // trade places with the dragged entry
  if (
    draggedEntry.targetResourceId === entry.resourceId &&
    concurrent.some(e => e.id === draggedEntry.entryId)
  ) {
    return draggedEntry.sourceResourceId;
  }
  // if there are more entries to the left than they can fit, shift it one to the right
  if (
    draggedEntry.targetResourceId < entry.resourceId &&
    draggedEntry.sourceResourceId >= draggedEntry.targetResourceId &&
    concurrent.some(e => wasPushedRight(e))
  ) {
    return entry.resourceId + 1;
  }
  // if there are empty spots to the left, move it there
  const numOccupiedColumnsLeft = new Set(
    concurrent.filter(e => e.resourceId < entry.resourceId).map(e => e.resourceId)
  ).size;
  if (
    numOccupiedColumnsLeft < entry.resourceId - 1 &&
    !concurrent.some(e => e.resourceId < entry.resourceId && e.id === draggedEntry.entryId)
  ) {
    return numOccupiedColumnsLeft + 1;
  }
  // if it is unrelated to the move action, we preserve its current resource id
  return entry.resourceId;
};

export function processEntries(entries, draggedEntry = null) {
  const topLevelEntries = entries.filter(e => !hasParent(e));
  const newEntries = entries.map(entry => ({
    ...entry,
    resourceId: getColumnId(entry, topLevelEntries, draggedEntry),
    parent:
      draggedEntry?.entryId === entry.id && hasParent(entry)
        ? getConcurrentEntries(entry, topLevelEntries).find(
            e => e.resourceId === draggedEntry.targetResourceId
          )?.id
        : entry.parent,
  }));
  const numColumns = _.max(newEntries.map(e => e.resourceId)) || 1;
  return [newEntries, [...Array(numColumns).keys()].map(n => ({id: n + 1}))];
}
