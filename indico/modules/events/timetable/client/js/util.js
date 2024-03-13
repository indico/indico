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
    return draggedEntry.id === block.id ? draggedEntry.targetcolumnId : block.columnId;
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

const updateEntries = (entries, newEntries) => [
  ...entries.map(e => {
    const update = newEntries.find(ne => e.id === ne.id);
    return update ? {...e, ...update} : e;
  }),
  ...newEntries.filter(ne => !entries.some(e => e.id === ne.id)),
];

export const applyChanges = (state, entryType = null) => {
  const {changes, currentChangeIdx, ...entries} = state;
  const effectiveChanges = _.isNumber(currentChangeIdx)
    ? changes.slice(0, currentChangeIdx)
    : changes;
  const newEntries = Object.entries(entries)
    .filter(([key, value]) => value && (!entryType || entryType === key))
    .map(([key, value]) => [
      key,
      effectiveChanges.reduce((acc, change) => updateEntries(acc, change[key] || []), value),
    ]);
  return entryType ? newEntries[0][1] : Object.fromEntries(newEntries);
};

const updateLastChange = (changes, newChange) => {
  const lastChange = changes[changes.length - 1];
  return [
    ...changes.slice(0, -1),
    {
      sessionBlocks: updateEntries(lastChange?.sessionBlocks || [], newChange.sessionBlocks || []),
      contributions: updateEntries(lastChange?.contributions || [], newChange.contributions || []),
    },
  ];
};

const addNewChange = (changes, newChange, currentChangeIdx) => [
  ...changes.slice(0, currentChangeIdx),
  newChange,
];

const resolveBlockConflicts = (sessionBlocks, changes, draggedEntry = null) => {
  const updatedBlocks = applyChanges({sessionBlocks, changes}).sessionBlocks;
  const conflictingBlock = updatedBlocks.find(
    block =>
      block.id !== draggedEntry?.id && // we avoid moving the dragged entry
      getConcurrentEntries(block, updatedBlocks).some(b => b.columnId === block.columnId)
  );
  if (!conflictingBlock) {
    return changes;
  }
  // if there is space on the left, move it there
  if (
    conflictingBlock.columnId > 1 &&
    !getConcurrentEntries(conflictingBlock, updatedBlocks).some(
      b => b.columnId === conflictingBlock.columnId - 1
    )
  ) {
    return resolveBlockConflicts(
      sessionBlocks,
      updateLastChange(changes, {
        sessionBlocks: [
          {
            id: conflictingBlock.id,
            columnId: conflictingBlock.columnId - 1,
          },
        ],
      }),
      draggedEntry
    );
  }
  // otherwise push it right
  return resolveBlockConflicts(
    [
      ...sessionBlocks.filter(
        b => b.id !== conflictingBlock.id && b.columnId <= conflictingBlock.columnId + 1
      ),
      sessionBlocks.find(b => b.id === conflictingBlock.id),
      ...sessionBlocks.filter(b => b.columnId > conflictingBlock.columnId + 1),
    ],
    updateLastChange(changes, {
      sessionBlocks: [
        {
          id: conflictingBlock.id,
          columnId: conflictingBlock.columnId + 1,
        },
      ],
    }),
    draggedEntry
  );
};

const removeBlockGaps = (sessionBlocks, changes) => {
  const updatedBlocks = applyChanges({sessionBlocks, changes}).sessionBlocks;
  const leftGapBlocks = updatedBlocks.filter(
    block =>
      block.columnId > 1 &&
      !getConcurrentEntries(block, updatedBlocks).some(b => b.columnId === block.columnId - 1)
  );
  if (leftGapBlocks.length === 0) {
    return changes;
  }
  return removeBlockGaps(
    sessionBlocks,
    updateLastChange(changes, {
      sessionBlocks: leftGapBlocks.map(b => ({id: b.id, columnId: b.columnId - 1})),
    })
  );
};

const processSessionBlocks = (state, draggedEntry = null) => {
  const {sessionBlocks, changes} = state;
  const updatedBlocks = applyChanges(state, 'sessionBlocks');
  return removeBlockGaps(
    sessionBlocks,
    resolveBlockConflicts(
      // it is important to keep the order of the blocks when resolving conflicts
      _.sortBy(sessionBlocks, 'columnId'),
      updateLastChange(changes, {
        sessionBlocks: updatedBlocks.flatMap(sessionBlock => {
          const columnId = getColumnId(sessionBlock, updatedBlocks, draggedEntry);
          return columnId === sessionBlock.columnId ? [] : [{id: sessionBlock.id, columnId}];
        }),
      }),
      draggedEntry
    )
  );
};

export const processEntries = (sessionBlocks, contributions, changes) => {
  const newBlocks = applyChanges({
    sessionBlocks,
    changes: processSessionBlocks({sessionBlocks, changes}),
  }).sessionBlocks;
  return {
    sessionBlocks: newBlocks,
    contributions,
  };
};

const moveBlock = (state, {event: block, start, end, resourceId: columnId}) => {
  const {changes, currentChangeIdx} = state;
  const newEntry = {id: block.id, start, end};
  const timeDiff = start - block.start;
  // if the dragged block has contributions, move them accordingly
  const newContribs = applyChanges(state, 'contributions')
    .filter(c => isChildOf(c, newEntry))
    .map(c => ({
      id: c.id,
      start: new Date(c.start.getTime() + timeDiff),
      end: new Date(c.end.getTime() + timeDiff),
    }));
  return {
    changes: processSessionBlocks(
      {
        ...state,
        changes: addNewChange(
          changes,
          {sessionBlocks: [newEntry], contributions: newContribs},
          currentChangeIdx
        ),
      },
      {
        id: block.id,
        sourcecolumnId: block.columnId,
        targetcolumnId: columnId,
      }
    ),
    currentChangeIdx: currentChangeIdx + 1,
  };
};

const resizeBlock = (state, {event: block, start, end, columnId}) => {
  const {changes, currentChangeIdx} = state;
  const contributions = applyChanges(state, 'contributions');
  const newEntry = {
    id: block.id,
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
  return {
    changes: processSessionBlocks(
      {...state, changes: addNewChange(changes, {sessionBlocks: [newEntry]}, currentChangeIdx)},
      {
        id: block.id,
        sourcecolumnId: block.columnId,
        targetcolumnId: columnId,
      }
    ),
    currentChangeIdx: currentChangeIdx + 1,
  };
};

const moveOrResizeContrib = (state, {event: contrib, start, end, resourceId: columnId}) => {
  const {changes, currentChangeIdx} = state;
  const {sessionBlocks, contributions} = applyChanges(state);
  const newContrib = {id: contrib.id, start, end, columnId};
  const newParent = getConcurrentEntries(newContrib, sessionBlocks).find(
    b => b.columnId === columnId && b.type === 'session'
  );
  // check if it's being dragged to outside of a block
  if (!newParent) {
    return {}; // TODO: turn this contrib into a top-level contrib
  }
  // check if it's being dragged to a block without enough space
  if (newContrib.start < newParent.start || newContrib.end > newParent.end) {
    return {};
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
        {id: c.id, start: last.end, end: new Date(last.end.getTime() + (c.end - c.start))},
      ];
    }, [prevContrib, newContrib].filter(c => c));
    // if they don't fit in the block, don't move anything
    if (rearrangedContribs[rearrangedContribs.length - 1].end > newParent.end) {
      return {};
    }
    return {
      changes: addNewChange(changes, {contributions: rearrangedContribs}, currentChangeIdx),
      currentChangeIdx: currentChangeIdx + 1,
    };
  }
  return {
    changes: addNewChange(changes, {contributions: [newContrib]}, currentChangeIdx),
    currentChangeIdx: currentChangeIdx + 1,
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
