// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

// TODO: remove second condition when we start using number ids
export const isContribution = entry => _.isNumber(entry.parent) || !!entry.parent;

export const hasContributions = (block, contribs) => contribs.some(e => e.parent === block.id);

export const getConcurrentEntries = (entry, entries) =>
  entries.filter(e => e.id !== entry.id && e.start < entry.end && e.end > entry.start);

const getColumnId = (entry, topLevelEntries, draggedEntry) => {
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

const processSessionBlocks = (sessionBlocks, draggedEntry = null) =>
  sessionBlocks.map(sessionBlock => ({
    ...sessionBlock,
    resourceId: getColumnId(sessionBlock, sessionBlocks, draggedEntry),
  }));

const processContributions = (contributions, sessionBlocks, draggedEntry = null) =>
  contributions.map(contrib => ({
    ...contrib,
    resourceId:
      draggedEntry?.entryId === contrib.id
        ? draggedEntry.targetResourceId
        : sessionBlocks.find(e => e.id === contrib.parent).resourceId,
    parent:
      draggedEntry?.entryId === contrib.id
        ? getConcurrentEntries(contrib, sessionBlocks).find(
            e => e.resourceId === draggedEntry.targetResourceId
          )?.id
        : contrib.parent,
  }));

export const processEntries = (sessionBlocks, contributions, draggedEntry = null) => {
  const newBlocks = processSessionBlocks(sessionBlocks, draggedEntry);
  return {
    sessionBlocks: newBlocks,
    contributions: processContributions(contributions, newBlocks, draggedEntry),
  };
};

const updateEntry = (entries, newEntry) => [...entries.filter(e => e.id !== newEntry.id), newEntry];

export const moveEntry = ({sessionBlocks, contributions}, {entryId, start, end, resourceId}) => {
  const entry =
    sessionBlocks.find(e => e.id === entryId) || contributions.find(e => e.id === entryId);
  const isContrib = isContribution(entry);
  const newEntry = {...entry, start, end};
  if (
    isContrib &&
    !getConcurrentEntries(newEntry, sessionBlocks).some(e => e.resourceId === resourceId)
  ) {
    return {sessionBlocks, contributions};
  }
  if (!isContrib && hasContributions(entry, contributions)) {
    // TODO: move all child contributions as well (by entry.start - start)
  }
  return processEntries(
    isContrib ? sessionBlocks : updateEntry(sessionBlocks, newEntry),
    isContrib ? updateEntry(contributions, newEntry) : contributions,
    {
      entryId,
      sourceResourceId: entry.resourceId,
      targetResourceId: resourceId || entry.resourceId,
    }
  );
};
