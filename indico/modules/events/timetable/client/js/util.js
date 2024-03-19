// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';

import {Translate} from 'indico/react/i18n';

export const entryColorSchema = PropTypes.shape({
  text: PropTypes.string,
  background: PropTypes.string,
});

export const entrySchema = PropTypes.shape({
  id: PropTypes.string.isRequired,
  type: PropTypes.oneOf(['session', 'contribution', 'break']).isRequired,
  title: PropTypes.string.isRequired,
  slotTitle: PropTypes.string, // only for sessions
  description: PropTypes.string,
  code: PropTypes.string,
  sessionCode: PropTypes.string, // only for sessions
  start: PropTypes.instanceOf(Date).isRequired,
  end: PropTypes.instanceOf(Date).isRequired,
  color: entryColorSchema,
  attachmentCount: PropTypes.number,
  displayOrder: PropTypes.number,
  parentId: PropTypes.string, // only for contributions
  columnId: PropTypes.number, // set only if parentId is null
});

export const formatTitle = (title, code) => (code ? `${title} (${code})` : title);

export const entryTypes = {
  session: {
    title: Translate.string('Session block'),
    icon: 'calendar alternate outline',
    formatTitle: e => `${formatTitle(e.title, e.code)}: ${formatTitle(e.slotTitle, e.sessionCode)}`,
  },
  contribution: {
    title: Translate.string('Contribution'),
    icon: 'file alternate outline',
    formatTitle: e => formatTitle(e.title, e.code),
  },
  break: {
    title: Translate.string('Break'),
    icon: 'coffee',
    formatTitle: e => formatTitle(e.title, e.code),
  },
};

export const hasContributions = (block, contribs) => contribs.some(e => e.parentId === block.id);
export const isChildOf = (contrib, block) => contrib.parentId === block.id;
const isConcurrent = (entry, other) =>
  entry.id !== other.id && entry.start < other.end && entry.end > other.start;
export const getConcurrentEntries = (entry, entries) => entries.filter(e => isConcurrent(entry, e));

const getColumnId = (block, blocks, draggedEntry = null) => {
  if (draggedEntry) {
    // if this is the dragged entry, assign it its targeted resource id
    return draggedEntry.id === block.id ? draggedEntry.targetcolumnId : block.columnId;
  }
  // if this is the first time we're assigning a resource id, we need check the desired display order
  const concurrent = getConcurrentEntries(block, blocks);
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

const dirtyMergeChanges = ({changes, currentChangeIdx}) =>
  changes
    .slice(0, currentChangeIdx)
    .reduce((acc, change) => updateEntries(acc, change), [])
    .map(c => (c.deleted ? _.pick(c, ['id', 'deleted']) : c));

export const mergeChanges = state => {
  const entries = [...state.blocks, ...state.children];
  return dirtyMergeChanges(state).flatMap(change => {
    const old = entries.find(e => e.id === change.id);
    const cleanChange = Object.fromEntries(
      Object.entries(change).filter(([k, v]) => !_.isEqual(v, old[k]))
    );
    return Object.keys(cleanChange).length > 0
      ? [{change: cleanChange, old, entry: {...old, ...change}}]
      : [];
  });
};

export const applyChanges = state => {
  const newEntries = updateEntries(
    [...(state.blocks || []), ...(state.children || [])],
    dirtyMergeChanges(state)
  ).filter(e => !e.deleted);
  const [blocks, children] = _.partition(newEntries, e => !e.parentId);
  return {blocks, children};
};

const updateLastChange = (changes, newChange) => [
  ...changes.slice(0, -1),
  updateEntries(changes[changes.length - 1] || [], newChange),
];

const addNewChange = ({changes, currentChangeIdx, ...entries}, newChange) => ({
  ...entries,
  changes: [...changes.slice(0, currentChangeIdx), newChange],
  currentChangeIdx: currentChangeIdx + 1,
});

const resolveBlockConflicts = (state, draggedEntry = null) => {
  const {blocks, changes} = state;
  const updatedBlocks = applyChanges(state).blocks;
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
      {
        ...state,
        changes: updateLastChange(changes, [
          {
            id: conflictingBlock.id,
            columnId: conflictingBlock.columnId - 1,
          },
        ]),
      },
      draggedEntry
    );
  }
  // otherwise push it right
  return resolveBlockConflicts(
    {
      ...state,
      blocks: [
        ...blocks.filter(
          b => b.id !== conflictingBlock.id && b.columnId <= conflictingBlock.columnId + 1
        ),
        blocks.find(b => b.id === conflictingBlock.id),
        ...blocks.filter(b => b.columnId > conflictingBlock.columnId + 1),
      ],
      changes: updateLastChange(changes, [
        {
          id: conflictingBlock.id,
          columnId: conflictingBlock.columnId + 1,
        },
      ]),
    },
    draggedEntry
  );
};

const removeBlockGaps = state => {
  const {blocks} = applyChanges(state);
  const leftGapBlocks = blocks.filter(
    block =>
      block.columnId > 1 &&
      !getConcurrentEntries(block, blocks).some(b => b.columnId === block.columnId - 1)
  );
  if (leftGapBlocks.length === 0) {
    return state.changes;
  }
  return removeBlockGaps({
    ...state,
    changes: updateLastChange(
      state.changes,
      leftGapBlocks.map(b => ({id: b.id, columnId: b.columnId - 1}))
    ),
  });
};

const layoutBlocks = (state, draggedEntry = null) => {
  const {blocks, changes, currentChangeIdx} = state;
  const updatedBlocks = applyChanges(state).blocks;
  // make sure all blocks have the correct column ID
  const columnChanges = updateLastChange(
    changes,
    updatedBlocks.flatMap(block => {
      const columnId = getColumnId(block, updatedBlocks, draggedEntry);
      return columnId === block.columnId ? [] : [{id: block.id, columnId}];
    })
  );
  // resolve conflicts between blocks in the same column
  const conflictChanges = resolveBlockConflicts(
    {
      ...state,
      // it is important to keep the order of the blocks when resolving conflicts
      blocks: _.sortBy(blocks, 'columnId'),
      changes: columnChanges,
    },
    draggedEntry
  );
  // remove any leftover gaps between blocks
  return {
    changes: removeBlockGaps({...state, changes: conflictChanges}),
    currentChangeIdx,
  };
};

export const preprocessEntries = (blocks, children, changes) => ({
  blocks: applyChanges({blocks, ...layoutBlocks({blocks, changes})}).blocks,
  children,
});

const moveBlock = (state, {event: block, start, end, resourceId: columnId}) => {
  const newEntry = {id: block.id};
  const timeDiff = start - block.start;
  if (timeDiff !== 0) {
    newEntry.start = start;
    newEntry.end = end;
  } else if (columnId === block.columnId) {
    return {};
  }
  // if a contribution with a parent is being moved, remove the parent
  if (block.parentId) {
    newEntry.parentId = null;
  }
  // if the dragged block has contributions, move them accordingly
  const newContribs = applyChanges(state)
    .children.filter(c => isChildOf(c, newEntry))
    .map(c => ({
      id: c.id,
      start: new Date(c.start.getTime() + timeDiff),
      end: new Date(c.end.getTime() + timeDiff),
    }));
  return layoutBlocks(addNewChange(state, [newEntry, ...newContribs]), {
    id: block.id,
    sourcecolumnId: block.columnId,
    targetcolumnId: columnId,
  });
};

const resizeBlock = (state, {event: block, start, end, resourceId: columnId}) => {
  const {children} = applyChanges(state);
  const newEntry = {id: block.id};
  const newStart = new Date(
    Math.min(
      ...children.filter(c => isChildOf(c, block)).map(c => c.start.getTime()),
      start.getTime()
    )
  );
  if (newStart.getTime() !== block.start.getTime()) {
    newEntry.start = newStart;
  }
  const newEnd = new Date(
    Math.max(...children.filter(c => isChildOf(c, block)).map(c => c.end.getTime()), end.getTime())
  );
  if (newEnd.getTime() !== block.end.getTime()) {
    newEntry.end = newEnd;
  }
  if (!newEntry.start && !newEntry.end) {
    return {};
  }
  return layoutBlocks(addNewChange(state, [newEntry]), {
    id: block.id,
    sourcecolumnId: block.columnId,
    targetcolumnId: columnId,
  });
};

const moveOrResizeContrib = (state, args) => {
  const {blocks, children} = applyChanges(state);
  const {event: contrib, start, end, resourceId} = args;

  const newContrib = {id: contrib.id, start, end, columnId: undefined};
  const newParent = getConcurrentEntries(newContrib, blocks).find(
    b => b.columnId === resourceId && b.type === 'session'
  );
  // check if it's being dragged to outside of a block
  if (!newParent) {
    return moveBlock(state, args);
  }
  // check if it's being dragged to a block without enough space
  if (newContrib.start < newParent.start || newContrib.end > newParent.end) {
    return {};
  }
  const newParentContribs = children.filter(c => c.id !== contrib.id && isChildOf(c, newParent));
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
    return addNewChange(state, rearrangedContribs);
  }
  return addNewChange(state, [newContrib]);
};

export const moveEntry = (state, args) =>
  args.event.type === 'contribution' ? moveOrResizeContrib(state, args) : moveBlock(state, args);

export const resizeEntry = (state, args) =>
  args.event.parentId ? moveOrResizeContrib(state, args) : resizeBlock(state, args);

export const deleteEntry = (state, entry) => {
  if (entry.parentId) {
    return addNewChange(state, [{id: entry.id, deleted: true}]);
  }
  const contribs = state.children.filter(c => isChildOf(c, entry));
  return layoutBlocks(
    addNewChange(state, [...contribs, entry].map(({id}) => ({id, deleted: true})))
  );
};

export const changeColor = (state, color) => {
  const {selectedId, blocks} = state;
  const selectedBlock = blocks.find(b => b.id === selectedId);
  return addNewChange(
    state,
    (_.isNumber(selectedBlock.sessionId)
      ? blocks.filter(b => b.sessionId === selectedBlock.sessionId)
      : [selectedBlock]
    ).map(({id}) => ({id, color}))
  );
};

export const getNumDays = (start, end) => Math.floor((end - start) / (24 * 60 * 60 * 1000));

export const resizeWindow = ({offset}, {newSize, dayIdx}) => {
  const newNumDays = Math.max(Math.floor((newSize - 210) / 110), 2);
  const numDaysOutOfBounds = dayIdx - newNumDays - offset + 1;
  return {
    numDays: newNumDays,
    offset: numDaysOutOfBounds > 0 ? offset + numDaysOutOfBounds : offset,
  };
};

// TODO remove
// eslint-disable-next-line no-alert
export const handleUnimplemented = () => alert('desole, ça marche pas encore :(');
