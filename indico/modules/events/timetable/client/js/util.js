// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';

import {Translate} from 'indico/react/i18n';

export const entryColorSchema = PropTypes.shape({
  text: PropTypes.string,
  background: PropTypes.string,
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
  placeholder: {},
};

export const entrySchema = PropTypes.shape({
  id: PropTypes.string.isRequired,
  type: PropTypes.oneOf(Object.keys(entryTypes)).isRequired,
  title: PropTypes.string, // required for all types except placeholder
  slotTitle: PropTypes.string, // only for sessions (required then)
  description: PropTypes.string,
  code: PropTypes.string,
  sessionCode: PropTypes.string, // only for sessions
  sessionId: PropTypes.number, // only for sessions
  contributionId: PropTypes.number, // only for contributions
  start: PropTypes.instanceOf(Date).isRequired,
  color: entryColorSchema,
  attachmentCount: PropTypes.number,
  displayOrder: PropTypes.number,
  parentId: PropTypes.string, // only for contributions
  columnId: PropTypes.number, // set only if parentId is null
  isPoster: PropTypes.bool, // only for contributions
});

export const hasContributions = (block, contribs) => contribs.some(e => e.parentId === block.id);
export const isChildOf = (contrib, block) => contrib.parentId === block.id;
export const getEndDt = entry => new Date(entry.start.getTime() + entry.duration * 60000);
const isConcurrent = (entry, other) =>
  entry.id !== other.id && entry.start < getEndDt(other) && getEndDt(entry) > other.start;
export const getConcurrentEntries = (entry, entries) => entries.filter(e => isConcurrent(entry, e));

/**
 * Calculates the column ID for a given block (top-level entry) based on the desired display order.
 * Intended to only be run when loading the entries for the first time.
 * @param {object} block Block to be assigned a column ID
 * @param {array} blocks All blocks
 * @returns {number} Column ID
 */
const getColumnId = (block, blocks) => {
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

/**
 * Updates an entries list with a list of new entries. Entries which are already present are
 * updated, while new entries are appended to the end. Partial-entries (such as changes) are
 * also supported, as long as the id attribute is present.
 * @param {array} entries Entries array
 * @param {array} newEntries New entries
 * @returns {array} Updated entries array
 */
const updateEntries = (entries, newEntries) => [
  ...entries.map(e => {
    const update = newEntries.find(ne => e.id === ne.id);
    return update ? {...e, ...update} : e;
  }),
  ...newEntries.filter(ne => !entries.some(e => e.id === ne.id)),
];

/**
 * Merges the changes in the changes array onto a single change list.
 * @param {object} state State of the timetable
 * @returns {array} Merged change list
 */
const dirtyMergeChanges = ({changes, currentChangeIdx}) =>
  changes
    .slice(0, currentChangeIdx)
    .reduce((acc, change) => updateEntries(acc, change), [])
    .map(c => (c.deleted ? _.pick(c, ['id', 'deleted']) : c));

/**
 * Merges the changes in the changes array onto a single change list, stripped of empty-changes and
 * unchanged values.
 * @param {object} state State of the timetable
 * @returns {array} Merged changes as an object of the change, old entry and updated entry
 */
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

/**
 * Applies the changes in the changes array to the timetable's entries
 * @param {object} state State of the timetable
 * @returns {object} {blocks, children} Updated blocks and child-entries
 */
export const applyChanges = state => {
  const newEntries = updateEntries(
    [...(state.blocks || []), ...(state.children || [])],
    dirtyMergeChanges(state)
  );
  const [unscheduled, scheduled] = _.partition(newEntries, 'deleted');
  const [children, blocks] = _.partition(scheduled, 'parentId');
  return {blocks, children, unscheduled: unscheduled.filter(e => e.type === 'contribution')};
};

/**
 * Appends the corresponding session's attributes to each entry in the array.
 * @param {array} entries Entries array
 * @param {Map} sessions Sessions map
 * @returns {array} Entries array with color attribute
 */
export const appendSessionAttributes = (entries, sessions) =>
  entries.map(e =>
    e.sessionId ? {...e, ..._.pick(sessions.get(e.sessionId), ['color', 'isPoster'])} : e
  );

/**
 * Updates the last entry of the changes array with a new change.
 * @param {array} changes Changes array
 * @param {object} newChange New change
 * @returns {array} Updated changes array
 */
const updateLastChange = (changes, newChange) => [
  ...changes.slice(0, -1),
  updateEntries(changes.at(-1) || [], newChange),
];

/**
 * Adds a change to the change array and increments the current change index.
 * @param {object} state State of the timetable
 * @param {object} newChange New change
 * @returns {object} The state with an updated changes array and an incremented currentChangeIdx
 */
const addNewChange = ({changes, currentChangeIdx, ...entries}, newChange) => ({
  ...entries,
  changes: [...changes.slice(0, currentChangeIdx), newChange],
  currentChangeIdx: currentChangeIdx + 1,
});

/**
 * Resolves any block conflicts (parallel top-level entries in the same column) by recursively
 * shifting all conflicting blocks with left-empty-space to the left, or otherwise to the right.
 * Child-entries are left untouched. Expects all blocks to have an assigned column.
 * @param {object} state State of the timetable
 * @param {object} draggedEntry Entry which was subject to the move/resize event, if applicable
 * @param {number} recursionCount Recursion count
 * @returns {array} Updated changes array
 */
const resolveBlockConflicts = (state, draggedEntry = null, recursionCount = 0) => {
  const {changes} = state;
  const updatedBlocks = applyChanges(state).blocks;
  const conflictingBlock = updatedBlocks.find(
    block =>
      block.id !== draggedEntry?.id && // we avoid moving the dragged entry
      getConcurrentEntries(block, updatedBlocks).some(b => b.columnId === block.columnId)
  );
  if (!conflictingBlock) {
    return changes;
  }
  if (recursionCount > updatedBlocks.length) {
    console.error('resolveBlockConflicts: recursion limit exceeded', conflictingBlock);
    return changes;
  }
  const {id, columnId} = conflictingBlock;
  const shift =
    columnId > 1 &&
    !getConcurrentEntries(conflictingBlock, updatedBlocks).some(b => b.columnId === columnId - 1)
      ? -1
      : 1;
  return resolveBlockConflicts(
    {...state, changes: updateLastChange(changes, [{id, columnId: columnId + shift}])},
    draggedEntry,
    recursionCount + 1
  );
};

/**
 * Removes any empty columns between parallel blocks (top-level entries) by recursively shifting all
 * blocks with left-empty-space to the left. Child-entries are left untouched. Expects all blocks to
 * have an assigned column.
 * @param {object} state State of the timetable
 * @param {array} ignoreIds Ids of the blocks to ignore
 * @param {number} recursionCount Recursion count
 * @returns {array} Updated changes array
 */
const removeBlockGaps = (state, ignoreIds = [], recursionCount = 0) => {
  const {changes} = state;
  const {blocks} = applyChanges(state);
  const leftGapBlocks = blocks.filter(
    block =>
      block.columnId > 1 &&
      !ignoreIds.includes(block.id) &&
      !getConcurrentEntries(block, blocks).some(
        b => b.columnId === block.columnId - 1 && !ignoreIds.includes(b.id)
      )
  );
  if (leftGapBlocks.length === 0) {
    return changes;
  }
  if (recursionCount > blocks.length) {
    console.error('removeBlockGaps: recursion limit exceeded', leftGapBlocks);
    return changes;
  }
  return removeBlockGaps(
    {
      ...state,
      changes: updateLastChange(
        changes,
        leftGapBlocks.map(b => ({id: b.id, columnId: b.columnId - 1}))
      ),
    },
    ignoreIds,
    recursionCount + 1
  );
};

/**
 * Performs the sorting of the entries onto the correct columns.
 * Starts by resolving block conflicts, and then removes any gaps between blocks. Child-entries are
 * left untouched.
 * @param {object} state State of the timetable
 * @param {object} draggedEntries {ids, targetColumnId} Entries which were subject a the move/resize event, if applicable
 * @returns {object} {changes, currentChangeIdx} Updated changes array and currentChangeIdx
 */
const layoutBlocks = (state, draggedEntries = null) => {
  let blocks = applyChanges(state).blocks;
  let changes = state.changes;
  // if the dragged entry is a block we do a pre-layout of the blocks before inserting it again
  if (draggedEntries && blocks.some(({id}) => draggedEntries.ids.includes(id))) {
    changes = removeBlockGaps(state, draggedEntries.ids);
    blocks = applyChanges({...state, changes}).blocks;
  }
  // make sure all blocks have the correct column ID
  changes = updateLastChange(
    changes,
    blocks.flatMap(block => {
      if (!draggedEntries) {
        return block.columnId ? [] : [{id: block.id, columnId: getColumnId(block, blocks)}];
      }
      const {ids, targetColumnId: columnId} = draggedEntries;
      // if this is the dragged entry, assign it its targeted resource id
      if (ids.includes(block.id)) {
        return [{id: block.id, columnId}];
      }
      // to preserve the order when resolving conflicts, we move everything right of the
      // dragged block one column to the right, and let removeBlockGaps compress it back
      return block.columnId > columnId ? [{id: block.id, columnId: block.columnId + 1}] : [];
    })
  );
  // resolve conflicts between blocks in the same column
  changes = resolveBlockConflicts(
    {
      ...state,
      changes,
    },
    draggedEntries
  );
  // remove any leftover gaps between blocks
  return {
    changes: removeBlockGaps({...state, changes}),
    currentChangeIdx: state.currentChangeIdx,
  };
};

/**
 * Performs the initial sorting of the entries onto the correct columns.
 * Same sorting as layoutBlocks, but saves the changes onto the blocks and children arrays directly
 * instead of polluting the changes array.
 * @param {array} blocks Blocks (top-level-entries) to be sorted
 * @param {array} children Child-entries to be sorted
 * @returns {object} {blocks, children} Sorted blocks and children
 */
export const preprocessEntries = (blocks, children, unscheduled) => ({
  blocks: applyChanges({blocks, ...layoutBlocks({blocks, changes: []})}).blocks,
  children,
  unscheduled,
});

/**
 * Moves a list of blocks (session, break or top-level contribution)
 * @param {object} state State of the timetable
 * @param {array} blocks Blocks to be moved
 * @param {number} columnId New column ID of the blocks.
 * @param {number} timeDiff Time difference of the blocks move. If unspecified, it is assumed that
 * the blocks have the updated start attribute.
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
const moveBlocks = (state, blocks, columnId, timeDiff = null) => {
  const newBlocks = timeDiff
    ? blocks.map(b => ({
        id: b.id,
        start: new Date(b.start.getTime() + timeDiff),
        deleted: false,
        parentId: null,
      }))
    : blocks;
  // if the dragged block has contributions, move them accordingly
  const newContribs = timeDiff
    ? applyChanges(state)
        .children.filter(c => newBlocks.some(b => isChildOf(c, b)))
        .map(c => ({
          id: c.id,
          start: new Date(c.start.getTime() + timeDiff),
        }))
    : [];
  console.debug('newContribs', newContribs, 'newBlocks', newBlocks);
  const changes = layoutBlocks(addNewChange(state, [...newBlocks, ...newContribs]), {
    ids: blocks.map(b => b.id),
    targetColumnId: columnId,
  });
  console.debug(changes);
  return changes;
};

/**
 * Moves a block (session, break or top-level contribution)
 * @param {object} state State of the timetable
 * @param {object} args {event, start, resourceId} Arguments from the move event
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
const moveBlock = (state, {event: block, start, resourceId: columnId}) => {
  const timeDiff = start - block.start;
  if (timeDiff === 0 && columnId === block.columnId) {
    return {};
  }
  return moveBlocks(state, [block], columnId, timeDiff);
};

/**
 * Resizes a block (session, break or top-level contribution)
 * @param {object} state State of the timetable
 * @param {object} args {event, start, end, resourceId} Arguments from the resize event
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
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
  const newEnd = block.isPoster
    ? end
    : new Date(
        Math.max(
          ...children.filter(c => isChildOf(c, block)).map(c => getEndDt(c).getTime()),
          end.getTime()
        )
      );
  if (newEnd.getTime() !== getEndDt(block).getTime()) {
    newEntry.duration = (newEnd.getTime() - newStart.getTime()) / 60000;
  }
  if (!newEntry.start && !newEntry.duration) {
    return {};
  }
  return layoutBlocks(addNewChange(state, [newEntry]), {ids: [block.id], targetColumnId: columnId});
};

/**
 * Rearranges contributions in a block in order to fit a new contribution
 * @param {array} rearranged Contributions to be rearranged
 * @param {array} inserted Contribution to be inserted
 * @returns {array|boolean} Rearranged contributions or false if they don't fit in the block
 */
const rearrangeContribsAfterMove = (rearranged, inserted) => {
  const prevContrib = rearranged.reduce(
    (acc, c) =>
      getEndDt(c) <= inserted[0].start && (!acc || getEndDt(c) > getEndDt(acc)) ? c : acc,
    null
  );
  const rearrangedContribs = _.sortBy(
    rearranged.filter(c => getEndDt(c) > inserted[0].start),
    'start'
  ).reduce(
    (acc, c) => [...acc, {id: c.id, start: getEndDt(acc.at(-1))}],
    [prevContrib, ...inserted].filter(c => c)
  );
  return rearrangedContribs;
};

/**
 * Moves a list of contributions
 * @param {object} state State of the timetable
 * @param {array} contribs Contributions to be moved
 * @param {Date} start New start date of the contributions
 * @param {number} columnId New column ID of the contributions
 * @param {number} gap Gap between the contributions
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
const moveContribs = (state, contribs, start, columnId, gap = 0) => {
  const {blocks, children} = applyChanges(state);

  const newContribs = contribs.reduce(
    (acc, c) => [
      ...acc,
      {
        id: c.id,
        start: acc.length > 0 ? new Date(getEndDt(acc.at(-1)).getTime() + gap * 60000) : start,
        duration: c.duration,
        columnId: null,
        deleted: false,
      },
    ],
    []
  );
  const parent = getConcurrentEntries(newContribs[0], blocks).find(
    b => b.columnId === columnId && b.type === 'session'
  );
  // check if it's being dragged to a block from a different session
  if (
    (parent &&
      (parent.sessionId !== contribs[0].sessionId || newContribs[0].start < parent.start)) ||
    (!parent && contribs[0].sessionId)
  ) {
    return {};
  }
  // check if it's being dragged to outside of a block or to a block without enough space
  if (!parent) {
    return moveBlocks(state, newContribs, columnId);
  }
  // if it's being dragged to a poster session, just schedule it at the beginning with the default duration
  if (parent?.isPoster) {
    return addNewChange(state, newContribs.map(c => ({...c, start})));
  }
  if (getEndDt(newContribs.at(-1)) > getEndDt(parent)) {
    // TODO resize block to fit all instead
    return moveBlocks(state, newContribs, columnId);
  }
  const parentContribs = children.filter(
    p => !contribs.some(c => p.id !== c.id) && isChildOf(p, parent)
  );
  newContribs.forEach(c => (c.parentId = parent.id));
  // if it's being dragged on top of a contribution, try to rearange them in order to fit
  const changes = parentContribs.some(p => newContribs.some(c => isConcurrent(p, c)))
    ? rearrangeContribsAfterMove(parentContribs, newContribs)
    : newContribs;
  // if they don't fit in the block, instead turn the contribs into a separate block
  if (getEndDt(changes.at(-1)) > getEndDt(parent)) {
    // TODO if scheduling multiple, resize block to fit all instead
    return moveBlocks(state, newContribs, columnId);
  }
  const newChanges = addNewChange(state, changes);
  // if the contrib used to be a block, it might have left a gap when moved
  if (!contribs[0].parentId) {
    return {changes: removeBlockGaps(newChanges), currentChangeIdx: newChanges.currentChangeIdx};
  }
  return newChanges;
};

/**
 * Moves a contribution
 * @param {object} state State of the timetable
 * @param {object} args {event, start, resourceId} Arguments from the move event
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
const moveContrib = (state, args) => {
  const {event: contrib, start, resourceId} = args;
  return moveContribs(state, [contrib], start, resourceId);
};

/**
 * Moves contributions that come before newContrib up in order to fit newContrib if necessary
 * @param {array} contribsBefore Contributions to be rearranged
 * @param {object} newContrib Contribution to be inserted
 * @returns {array} Changes to the contributions, ordered by start date
 */
const moveUp = (contribsBefore, newContrib) => {
  const changes = [newContrib];
  for (const contrib of [...contribsBefore].reverse()) {
    if (changes.at(-1).start < getEndDt(contrib)) {
      const diff = changes.at(-1).start - getEndDt(contrib);
      changes.push({
        id: contrib.id,
        start: new Date(contrib.start.getTime() + diff),
      });
    } else {
      changes.push(contrib);
    }
  }
  return changes.slice(1).reverse();
};

/**
 * Moves contributions that come after newContrib down in order to fit newContrib if necessary
 * @param {array} contribsBefore Contributions to be rearranged
 * @param {object} newContrib Contribution to be inserted
 * @returns {array} Changes to the contributions, ordered by start date
 */
const moveDown = (contribsAfter, newContrib) => {
  const changes = [newContrib];
  for (const contrib of contribsAfter) {
    if (getEndDt(changes.at(-1)) > contrib.start) {
      const diff = getEndDt(changes.at(-1)) - contrib.start;
      changes.push({
        id: contrib.id,
        start: new Date(contrib.start.getTime() + diff),
      });
    } else {
      changes.push(contrib);
    }
  }
  return changes.slice(1);
};

/**
 * Rearranges contributions in a block in order to fit a new contribution after one of the contributions
 * has been resized in either direction.
 * @param {array} contribs Contributions to be rearranged
 * @param {object} contrib Contribution to be inserted
 * @param {object} oldContrib The old contribution that was resized
 * @returns {array} Changes to the contributions, ordered by start date
 */
const rearrangeContribsAfterResize = (contribs, contrib, oldContrib) => {
  contribs = _.sortBy(contribs, 'start'); // contribs are not guaranteed to be sorted
  const contribsBefore = contribs.filter(c => getEndDt(c) <= oldContrib.start);
  const contribsAfter = contribs.filter(c => c.start >= getEndDt(oldContrib));

  return [...moveUp(contribsBefore, contrib), contrib, ...moveDown(contribsAfter, contrib)];
};

/**
 * Resizes a child-entry
 * @param {object} state State of the timetable
 * @param {object} args {event, start, end, resourceId} Arguments from the resize event
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
const resizeChild = (state, args) => {
  const {blocks, children} = applyChanges(state);
  const {event: child, start, end} = args;

  const newContrib = {
    id: child.id,
    start,
    duration: (end.getTime() - start.getTime()) / 60000,
  };
  const parent = blocks.find(b => isChildOf(child, b));
  const parentContribs = children.filter(c => c.id !== child.id && isChildOf(c, parent));
  const hasCollisions = parentContribs.some(c => isConcurrent(c, newContrib));

  // there are collisions, try to rearange them in order to fit
  const newContribs = hasCollisions
    ? rearrangeContribsAfterResize(parentContribs, newContrib, child)
    : [newContrib];

  // if they don't fit in the block, extend the block
  if (getEndDt(newContribs.at(-1)) > getEndDt(parent)) {
    return layoutBlocks(
      addNewChange(state, [
        ...newContribs,
        {
          id: parent.id,
          duration: (getEndDt(newContribs.at(-1)).getTime() - parent.start.getTime()) / 60000,
        },
      ])
    );
  } else if (newContribs[0].start < parent.start) {
    return layoutBlocks(
      addNewChange(state, [...newContribs, {id: parent.id, start: newContribs[0].start}])
    );
  }
  return addNewChange(state, newContribs);
};

/**
 * Moves an entry.
 * @param {object} state State of the timetable
 * @param {object} args {event, start, end, resourceId} Arguments from the move event
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
export const moveEntry = (state, args) =>
  args.event.type === 'contribution' ? moveContrib(state, args) : moveBlock(state, args);

/**
 * Resizes an entry
 * @param {object} state State of the timetable
 * @param {object} args {event, start, end, resourceId} Arguments from the resize event
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
export const resizeEntry = (state, args) =>
  args.event.parentId ? resizeChild(state, args) : resizeBlock(state, args);

/**
 * Deletes an entry
 * @param {object} state State of the timetable
 * @param {object} entry Entry to be deleted
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
export const deleteEntry = (state, entry) => {
  if (entry.parentId) {
    return addNewChange(state, [{id: entry.id, deleted: true}]);
  }
  const contribs = state.children.filter(c => isChildOf(c, entry));
  return layoutBlocks(
    addNewChange(state, [...contribs, entry].map(({id}) => ({id, deleted: true})))
  );
};

/**
 * Schedules a list of contributions
 * @param {object} state State of the timetable
 * @param {array} contribs Contributions to be scheduled
 * @param {object} args {start, resource} Arguments from the Calendar's drop event
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
export const dropUnscheduledContribs = (state, contribs, {start, resource}) => {
  return moveContribs(state, contribs, start, resource);
};

/**
 * Schedules a list of contributions
 * @param {object} state State of the timetable
 * @param {array} contribs Contributions to be scheduled
 * @param {number} gap Gap between contributions in minutes
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
export const scheduleContribs = (state, contribs, gap) => {
  const {blocks} = applyChanges(state);
  const selectedBlock = state.selectedId && blocks.find(b => b.id === state.selectedId);
  const parent = selectedBlock?.type === 'session' ? selectedBlock : null;
  const resource = selectedBlock?.columnId || 1;
  // TODO if the set is empty, schedule all unscheduled from the session
  // TODO fix start datetime (based on selected day)
  const start = parent?.start || (selectedBlock && getEndDt(selectedBlock)) || new Date();
  return moveContribs(state, contribs, start, resource, gap);
};

/**
 * Changes the color of the selected Break block
 * @param {object} state State of the timetable
 * @param {object} color New color
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
export const changeBreakColor = (state, color) => {
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

/**
 * Changes the color of the selected block (of type session or break)
 * @param {object} state State of the timetable
 * @param {object} color New color
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
export const changeSessionColor = (sessions, sessionId, color) => {
  const newSessions = new Map(sessions);
  return newSessions.set(sessionId, {...sessions.get(sessionId), color});
};

/**
 * Get the number of days between two dates
 * @param {Date} start Starting date
 * @param {Date} end Ending date
 * @returns {number} Number of days between two dates
 */
export const getNumDays = (start, end) => moment(end).diff(moment(start), 'days');

/**
 * Calculates the updates to the state of the navbar after a window resize event
 * @param {object} state State of the navbar
 * @param {object} action {newSize, dayIdx} New window size and selected day's index
 * @returns {object} {numDays, offset} Number of days that fit on the toolbar and offset necessary
 * to make the selected day visible
 */
export const resizeWindow = ({offset}, {newSize, dayIdx}) => {
  const numDays = Math.max(Math.floor((newSize - 340) / 110), 2);
  const numDaysOutOfBounds = dayIdx - numDays - offset + 1;
  return {numDays, offset: numDaysOutOfBounds > 0 ? offset + numDaysOutOfBounds : offset};
};

// TODO remove
// eslint-disable-next-line no-alert
export const handleUnimplemented = () => alert('desole, ça marche pas encore :(');
