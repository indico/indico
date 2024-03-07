// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

export const hasContributions = (block, contribs) => contribs.some(e => e.parentId === block.id);
export const isChildOf = (contrib, block) => contrib.parentId === block.id;
const isConcurrent = (entry, other) =>
  entry.id !== other.id && entry.start < other.end && entry.end > other.start;
export const getConcurrentEntries = (entry, entries) => entries.filter(e => isConcurrent(entry, e));

const getColumnId = (block, sessionBlocks, draggedEntry = null) => {
  if (draggedEntry) {
    // if this is the dragged entry, assign it its targeted resource id
    return draggedEntry.id === block.id ? draggedEntry.targetResourceId : block.resourceId;
  }
  // if this is the first time we're assigning a resource id, we need check the desired display order
  const concurrent = getConcurrentEntries(block, sessionBlocks);
  const [orderedConcurrent, unorderedConcurrent] = _.partition([...concurrent, block], e =>
    _.isNumber(e.displayOrder)
  );
  return _.isNumber(block.displayOrder)
    ? _.sortBy(orderedConcurrent, 'displayOrder').findIndex(e => e.id === block.id) + 1
    : _.sortBy(unorderedConcurrent, ['code', 'title']).findIndex(e => e.id === block.id) +
        orderedConcurrent.length +
        1;
};

const updateEntries = (entries, newEntry) =>
  Array.isArray(newEntry)
    ? [...entries.filter(e => !newEntry.some(ne => e.id === ne.id)), ...newEntry]
    : [...entries.filter(e => e.id !== newEntry.id), newEntry];

const resolveBlockConflicts = (sessionBlocks, draggedEntry = null) => {
  const conflictingBlock = sessionBlocks.find(
    block =>
      block.id !== draggedEntry?.id && // we avoid moving the dragged entry
      getConcurrentEntries(block, sessionBlocks).some(b => b.resourceId === block.resourceId)
  );
  if (!conflictingBlock) {
    return sessionBlocks;
  }
  // if there is space on the left, move it there
  if (
    conflictingBlock.resourceId > 1 &&
    !getConcurrentEntries(conflictingBlock, sessionBlocks).some(
      b => b.resourceId === conflictingBlock.resourceId - 1
    )
  ) {
    return resolveBlockConflicts(
      updateEntries(sessionBlocks, {
        ...conflictingBlock,
        resourceId: conflictingBlock.resourceId - 1,
      }),
      draggedEntry
    );
  }
  // otherwise push it right
  return resolveBlockConflicts(
    [
      ...sessionBlocks.filter(
        b => b.id !== conflictingBlock.id && b.resourceId <= conflictingBlock.resourceId + 1
      ),
      {...conflictingBlock, resourceId: conflictingBlock.resourceId + 1},
      ...sessionBlocks.filter(b => b.resourceId > conflictingBlock.resourceId + 1),
    ],
    draggedEntry
  );
};

const removeBlockGaps = sessionBlocks => {
  const leftGapBlocks = sessionBlocks.filter(
    block =>
      block.resourceId > 1 &&
      !getConcurrentEntries(block, sessionBlocks).some(b => b.resourceId === block.resourceId - 1)
  );
  if (leftGapBlocks.length === 0) {
    return sessionBlocks;
  }
  return removeBlockGaps(
    updateEntries(sessionBlocks, leftGapBlocks.map(b => ({...b, resourceId: b.resourceId - 1})))
  );
};

const processSessionBlocks = (sessionBlocks, draggedEntry = null) =>
  removeBlockGaps(
    resolveBlockConflicts(
      // it is important to keep the order of the blocks when resolving conflicts
      _.sortBy(
        sessionBlocks.map(sessionBlock => ({
          ...sessionBlock,
          resourceId: getColumnId(sessionBlock, sessionBlocks, draggedEntry),
        })),
        'resourceId'
      ),
      draggedEntry
    )
  );

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

const moveBlock = ({sessionBlocks, contributions}, {event: block, start, end, resourceId}) => {
  const newEntry = {...block, start, end};
  const timeDiff = start - block.start;
  // if the dragged block has contributions, move them accordingly
  const newContribs = contributions.map(c =>
    isChildOf(c, newEntry)
      ? {
          ...c,
          start: new Date(c.start.getTime() + timeDiff),
          end: new Date(c.end.getTime() + timeDiff),
        }
      : c
  );
  return processEntries(updateEntries(sessionBlocks, newEntry), newContribs, {
    id: block.id,
    sourceResourceId: block.resourceId,
    targetResourceId: resourceId,
  });
};

const resizeBlock = ({sessionBlocks, contributions}, {event: block, start, end, resourceId}) => {
  const newEntry = {
    ...block,
    start: new Date(
      Math.min(
        ...contributions.filter(c => isChildOf(c, block)).map(c => c.start.getTime()),
        start.getTime()
      )
    ),
    end: new Date(
      Math.max(
        ...contributions.filter(c => isChildOf(c, block)).map(c => c.end.getTime()),
        end.getTime()
      )
    ),
  };
  return processEntries(updateEntries(sessionBlocks, newEntry), contributions, {
    id: block.id,
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
    b => b.resourceId === resourceId && b.type === 'session'
  );
  // check if it's being dragged to outside of a block or a block without enough space
  if (!newParent || newContrib.start < newParent.start || newContrib.end > newParent.end) {
    return {sessionBlocks, contributions};
  }
  const newParentContribs = contributions.filter(
    c => c.id !== contrib.id && isChildOf(c, newParent)
  );
  newContrib.parentId = newParent.id;
  // if it's being dragged on top of a contribution, try to rearange them in order to fit
  if (newParentContribs.some(c => isConcurrent(c, newContrib))) {
    const prevContrib = newParentContribs.reduce(
      (acc, c) => (c.end <= newContrib.start && (!acc || c.end > acc.end) ? c : acc),
      null
    );
    const rearrangedContribs = _.sortBy(
      newParentContribs.filter(c => c.end > newContrib.start),
      'start'
    ).reduce((acc, c) => {
      const last = acc[acc.length - 1];
      return [
        ...acc,
        {...c, start: last.end, end: new Date(last.end.getTime() + (c.end - c.start))},
      ];
    }, [prevContrib, newContrib].filter(c => c));
    // if they don't fit in the block, don't move anything
    if (rearrangedContribs[rearrangedContribs.length - 1].end > newParent.end) {
      return {sessionBlocks, contributions};
    }
    return {
      sessionBlocks,
      contributions: updateEntries(contributions, rearrangedContribs),
    };
  }
  return {
    sessionBlocks,
    contributions: updateEntries(contributions, newContrib),
  };
};

export const moveEntry = (entries, args) =>
  args.event.type === 'contribution'
    ? moveOrResizeContrib(entries, args)
    : moveBlock(entries, args);

export const resizeEntry = (entries, args) =>
  args.event.type === 'contribution'
    ? moveOrResizeContrib(entries, args)
    : resizeBlock(entries, args);

export const getNumDays = (start, end) => Math.floor((end - start) / (24 * 60 * 60 * 1000));

export const resizeWindow = ({offset}, {newSize, dayIdx}) => {
  const newNumDays = Math.max(Math.floor((newSize - 210) / 110), 2);
  const numDaysOutOfBounds = dayIdx - newNumDays - offset + 1;
  return {
    numDays: newNumDays,
    offset: numDaysOutOfBounds > 0 ? offset + numDaysOutOfBounds : offset,
  };
};
