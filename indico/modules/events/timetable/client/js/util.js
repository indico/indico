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

// TODO get this from the server - contribution_settings.get('default_duration')
const CONTRIB_DEFAULT_DURATION = 20; // in minutes

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
  end: PropTypes.instanceOf(Date).isRequired,
  color: entryColorSchema,
  attachmentCount: PropTypes.number,
  displayOrder: PropTypes.number,
  parentId: PropTypes.string, // only for contributions
  columnId: PropTypes.number, // set only if parentId is null
  isPoster: PropTypes.bool, // only for contributions
});

export const hasContributions = (block, contribs) => contribs.some(e => e.parentId === block.id);
export const isChildOf = (contrib, block) => contrib.parentId === block.id;
const isConcurrent = (entry, other) =>
  entry.id !== other.id && entry.start < other.end && entry.end > other.start;
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
 * Updates the last entry of the changes array with a new change.
 * @param {array} changes Changes array
 * @param {object} newChange New change
 * @returns {array} Updated changes array
 */
const updateLastChange = (changes, newChange) => [
  ...changes.slice(0, -1),
  updateEntries(changes[changes.length - 1] || [], newChange),
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
 * @param {string} ignoreId Id of a block to ignore
 * @param {number} recursionCount Recursion count
 * @returns {array} Updated changes array
 */
const removeBlockGaps = (state, ignoreId = null, recursionCount = 0) => {
  const {changes} = state;
  const {blocks} = applyChanges(state);
  const leftGapBlocks = blocks.filter(
    block =>
      block.columnId > 1 &&
      block.id !== ignoreId &&
      !getConcurrentEntries(block, blocks).some(
        b => b.columnId === block.columnId - 1 && b.id !== ignoreId
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
    ignoreId,
    recursionCount + 1
  );
};

/**
 * Performs the sorting of the entries onto the correct columns.
 * Starts by resolving block conflicts, and then removes any gaps between blocks. Child-entries are
 * left untouched.
 * @param {object} state State of the timetable
 * @param {object} draggedEntry Entry which was subject to the move/resize event, if applicable
 * @returns {object} {changes, currentChangeIdx} Updated changes array and currentChangeIdx
 */
const layoutBlocks = (state, draggedEntry = null) => {
  let blocks = applyChanges(state).blocks;
  let changes = state.changes;
  // if the dragged entry is a block we do a pre-layout of the blocks before inserting it again
  if (draggedEntry && blocks.some(({id}) => id === draggedEntry.id)) {
    changes = removeBlockGaps(state, draggedEntry.id);
    blocks = applyChanges({...state, changes}).blocks;
  }
  // make sure all blocks have the correct column ID
  changes = updateLastChange(
    changes,
    blocks.flatMap(block => {
      if (!draggedEntry) {
        return block.columnId ? [] : [{id: block.id, columnId: getColumnId(block, blocks)}];
      }
      const {id, targetcolumnId: columnId} = draggedEntry;
      // if this is the dragged entry, assign it its targeted resource id
      if (id === block.id) {
        return [{id, columnId}];
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
    draggedEntry
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
export const preprocessEntries = (blocks, children) => ({
  blocks: applyChanges({blocks, ...layoutBlocks({blocks, changes: []})}).blocks,
  children,
});

/**
 * Moves a block (session, break or top-level contribution)
 * @param {object} state State of the timetable
 * @param {object} args {event, start, end, resourceId} Arguments from the move event
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
const moveBlock = (state, {event: block, start, end, resourceId: columnId}) => {
  const newEntry = {id: block.id, start, end, deleted: false};
  const timeDiff = start - block.start;
  if (timeDiff === 0 && columnId === block.columnId) {
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

/**
 * Rearranges contributions in a block in order to fit a new contribution
 * @param {array} contribs Contributions to be rearranged
 * @param {object} contrib Contribution to be inserted
 * @returns {array|boolean} Rearranged contributions or false if they don't fit in the block
 */
const rearrangeContribsAfterMove = (contribs, contrib) => {
  const prevContrib = contribs.reduce(
    (acc, c) => (c.end <= contrib.start && (!acc || c.end > acc.end) ? c : acc),
    null
  );
  const rearrangedContribs = _.sortBy(contribs.filter(c => c.end > contrib.start), 'start').reduce(
    (acc, c) => {
      const last = acc[acc.length - 1];
      return [
        ...acc,
        {id: c.id, start: last.end, end: new Date(last.end.getTime() + (c.end - c.start))},
      ];
    },
    [prevContrib, contrib].filter(c => c)
  );
  return rearrangedContribs;
};

/**
 * Moves a contribution
 * @param {object} state State of the timetable
 * @param {object} args {event, start, end, resourceId} Arguments from the move event
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
const moveContrib = (state, args) => {
  const {blocks, children} = applyChanges(state);
  const {event: contrib, start, end, resourceId} = args;

  const newContrib = {id: contrib.id, start, end, columnId: undefined, deleted: false};
  const parent = getConcurrentEntries(newContrib, blocks).find(
    b => b.columnId === resourceId && b.type === 'session'
  );
  // check if it's being dragged to outside of a block or to a block without enough space
  if (!parent || newContrib.start < parent.start || newContrib.end > parent.end) {
    return moveBlock(state, args);
  }
  const parentContribs = children.filter(c => c.id !== contrib.id && isChildOf(c, parent));
  newContrib.parentId = parent.id;
  // if it's being dragged on top of a contribution, try to rearange them in order to fit
  const newContribs = parentContribs.some(c => isConcurrent(c, newContrib))
    ? rearrangeContribsAfterMove(parentContribs, newContrib)
    : [newContrib];
  // if they don't fit in the block, instead turn the contrib into a separate block
  if (newContribs[newContribs.length - 1].end > parent.end) {
    return moveBlock(state, args);
  }
  const newChanges = addNewChange(state, newContribs);
  // if the contrib used to be a block, it might have left a gap when moved
  if (!contrib.parentId) {
    return {changes: removeBlockGaps(newChanges), currentChangeIdx: newChanges.currentChangeIdx};
  }
  return newChanges;
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
    if (changes.at(-1).start < contrib.end) {
      const diff = changes.at(-1).start - contrib.end;
      changes.push({
        id: contrib.id,
        start: new Date(contrib.start.getTime() + diff),
        end: new Date(contrib.end.getTime() + diff),
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
    if (changes.at(-1).end > contrib.start) {
      const diff = changes.at(-1).end - contrib.start;
      changes.push({
        id: contrib.id,
        start: new Date(contrib.start.getTime() + diff),
        end: new Date(contrib.end.getTime() + diff),
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
  const contribsBefore = contribs.filter(c => c.end <= oldContrib.start);
  const contribsAfter = contribs.filter(c => c.start >= oldContrib.end);

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

  const newContrib = {id: child.id, start, end};
  const parent = blocks.find(b => isChildOf(child, b));
  const parentContribs = children.filter(c => c.id !== child.id && isChildOf(c, parent));
  const hasCollisions = parentContribs.some(c => isConcurrent(c, newContrib));

  // there are collisions, try to rearange them in order to fit
  const newContribs = hasCollisions
    ? rearrangeContribsAfterResize(parentContribs, newContrib, child)
    : [newContrib];

  // if they don't fit in the block, extend the block
  if (newContribs.at(-1).end > parent.end) {
    return layoutBlocks(
      addNewChange(state, [...newContribs, {id: parent.id, end: newContribs.at(-1).end}])
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
 * Schedules a contribution
 * @param {object} state State of the timetable
 * @param {object} contrib Contribution to be scheduled
 * @param {object} args {start, end, resource} Arguments from the schedule event
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
export const scheduleContrib = (state, contrib, {start, end, resource}) => {
  console.debug('scheduleContrib', state, contrib, {start, end, resource});
  return moveContrib(state, {
    start,
    end: new Date(start.getTime() + CONTRIB_DEFAULT_DURATION * 60000),
    event: contrib,
    resourceId: resource,
  });
};

/**
 * Changes the color of the selected block (of type session or break)
 * @param {object} state State of the timetable
 * @param {object} color New color
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
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
