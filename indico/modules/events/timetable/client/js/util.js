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
const isChildOf = (contrib, block) => contrib.parent === block.id;
const isConcurrent = (entry, other) =>
  entry.id !== other.id && entry.start < other.end && entry.end > other.start;
export const getConcurrentEntries = (entry, entries) => entries.filter(e => isConcurrent(entry, e));

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

const processContributions = (contributions, sessionBlocks) =>
  contributions.map(contrib => ({
    ...contrib,
    resourceId: sessionBlocks.find(block => isChildOf(contrib, block)).resourceId,
  }));

export const processEntries = (sessionBlocks, contributions, draggedEntry = null) => {
  const newBlocks = processSessionBlocks(sessionBlocks, draggedEntry);
  return {
    sessionBlocks: newBlocks,
    contributions: processContributions(contributions, newBlocks),
  };
};

const updateEntry = (entries, newEntry) => [...entries.filter(e => e.id !== newEntry.id), newEntry];

const moveOrResizeBlock = (
  {sessionBlocks, contributions},
  {event: block, start, end, resourceId}
) => {
  const newEntry = {...block, start, end};
  let newContribs = contributions;
  // if the dragged block has contributions, move them accordingly and stretch it if necessary
  if (hasContributions(block, contributions)) {
    const timeDiff = start - block.start;
    newContribs = contributions.map(c =>
      isChildOf(c, newEntry)
        ? {
            ...c,
            start: new Date(c.start.getTime() + timeDiff),
            end: new Date(c.end.getTime() + timeDiff),
          }
        : c
    );
    newEntry.end = new Date(
      Math.max(
        ...newContribs.filter(c => isChildOf(c, newEntry)).map(c => c.end.getTime()),
        end.getTime()
      )
    );
  }
  return processEntries(updateEntry(sessionBlocks, newEntry), newContribs, {
    entryId: block.id,
    sourceResourceId: block.resourceId,
    targetResourceId: resourceId,
  });
};

const moveOrResizeContrib = (
  {sessionBlocks, contributions},
  {event: contrib, start, end, resourceId}
) => {
  const newContrib = {...contrib, start, end, resourceId};
  const newParent = getConcurrentEntries(newContrib, sessionBlocks).find(
    b => b.resourceId === resourceId
  );
  // check if its being dragged to outside of a block or a block without enough space
  if (
    !newParent ||
    contributions.some(c => isChildOf(c, newParent) && isConcurrent(c, newContrib)) ||
    newContrib.start < newParent.start ||
    newContrib.end > newParent.end
  ) {
    return {sessionBlocks, contributions};
  }
  newContrib.parent = newParent.id;
  return {
    sessionBlocks,
    contributions: updateEntry(contributions, newContrib),
  };
};

export const moveOrResizeEntry = (entries, args) =>
  isContribution(args.event)
    ? moveOrResizeContrib(entries, args)
    : moveOrResizeBlock(entries, args);

export const getNumDays = (start, end) => Math.floor((end - start) / (24 * 60 * 60 * 1000));

export const resizeWindow = ({offset}, {newSize, dayIdx}) => {
  const newNumDays = Math.max(Math.floor((newSize - 210) / 110), 2);
  const numDaysOutOfBounds = dayIdx - newNumDays - offset + 1;
  return {
    numDays: newNumDays,
    offset: numDaysOutOfBounds > 0 ? offset + numDaysOutOfBounds : offset,
  };
};
