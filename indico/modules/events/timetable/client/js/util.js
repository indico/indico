// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import noOverlap from 'react-big-calendar/lib/utils/layout-algorithms/no-overlap';

// TODO: remove second condition when we start using number ids
const hasParent = event => _.isNumber(event.parent) || event.parent;

const getConcurrentEntries = (entries, entry) =>
  entries.filter(e => e.start < entry.end && e.end > entry.start);

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
  const concurrent = getConcurrentEntries(topLevelEntries, entry);
  if (concurrent.length === 1) {
    return 1;
  }
  if (draggedEntry) {
    // if this is the dragged entry, assign it its targeted resource id
    if (draggedEntry.entryId === entry.id) {
      return draggedEntry.targetResourceId;
    }
    const wasPushedRight = e => {
      const c = e.id === entry.id ? concurrent : getConcurrentEntries(topLevelEntries, e);
      return (
        draggedEntry.entryId !== e.id &&
        draggedEntry.targetResourceId === e.resourceId &&
        draggedEntry.sourceResourceId >= draggedEntry.targetResourceId &&
        c.some(
          ev =>
            ev.id === draggedEntry.entryId ||
            (ev.id !== e.id && e.resourceId === draggedEntry.sourceResourceId)
        )
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
      concurrent.some(e => e.id !== entry.id && wasPushedRight(e))
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
  }
  const [orderedConcurrent, unorderedConcurrent] = _.partition(concurrent, e =>
    _.isNumber(e.displayOrder)
  );
  const sortedOrderedConcurrent = _.sortBy(orderedConcurrent, 'displayOrder');
  const sortedUnorderedConcurrent = _.sortBy(unorderedConcurrent, ['code', 'title']);
  return _.isNumber(entry.displayOrder)
    ? sortedOrderedConcurrent.findIndex(e => e.id === entry.id) + 1
    : sortedUnorderedConcurrent.findIndex(e => e.id === entry.id) +
        sortedOrderedConcurrent.length +
        1;
};

export function processEntries(entries, draggedEntry = null) {
  const topLevelEvents = entries.filter(e => !hasParent(e));
  const newEvents = entries.map(event => ({
    ...event,
    resourceId: getColumnId(event, topLevelEvents, draggedEntry),
  }));
  const numColumns = _.max(newEvents.map(e => e.resourceId)) || 1;
  return [newEvents, [...Array(numColumns).keys()].map(n => ({id: n + 1}))];
}

const makeTranslucent = hex => {
  if (!hex) {
    return undefined;
  }
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, 0.8)`;
};

export const entryStyleGetter = entries => entry => {
  if (hasParent(entry)) {
    const parent = entries.find(e => e.id === entry.parent);
    return {
      style: {
        color: parent.color?.text,
        backgroundColor: makeTranslucent(parent.color?.background),
        borderColor: makeTranslucent(parent.color?.background),
        borderTopLeftRadius: 0,
        borderBottomLeftRadius: 0,
        borderLeftWidth: 0,
        zIndex: 1,
      },
    };
  }
  const hasChild = entries.some(e => e.parent === entry.id);
  return {
    style: {
      color: entry.color?.text,
      backgroundColor: entry.color?.background,
      borderColor: entry.color?.background,
      borderTopRightRadius: hasChild ? 0 : undefined,
      borderBottomRightRadius: hasChild ? 0 : undefined,
      zIndex: 1,
    },
  };
};

export const layoutAlgorithm = (allEntries, numColumns) => props =>
  noOverlap(props).map(styledEntry => {
    // if it's a child-entry, remove the padding
    if (hasParent(styledEntry.event)) {
      const style = {
        ...styledEntry.style,
        width: `calc(${styledEntry.size}%)`,
        xOffset: `calc(${styledEntry.style.left}%)`,
      };
      return {...styledEntry, style};
    }
    // make entries take up the full width if there are no concurrencies
    if (getConcurrentEntries(allEntries, styledEntry.event).length > 1) {
      return styledEntry;
    }
    const size = 100 * numColumns;
    const padding = 10 * (numColumns - 1) - (styledEntry.idx === 0 ? 0 : 3);
    const style = {...styledEntry.style, width: `calc(${size}% + ${padding}px)`};
    return {...styledEntry, size, style};
  });
