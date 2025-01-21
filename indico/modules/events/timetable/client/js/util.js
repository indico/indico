// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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

export const formatTitle = (title, code) => (code ? `${title} (${code})` : title);

export const entryTypes = {
  block: {
    title: Translate.string('Session block'),
    icon: 'calendar alternate outline',
    formatTitle: e => `${formatTitle(e.title, e.code)}: ${formatTitle(e.slotTitle, e.sessionCode)}`,
  },
  contrib: {
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

export const entrySchema = PropTypes.shape({
  id: PropTypes.number.isRequired,
  type: PropTypes.oneOf(Object.keys(entryTypes)).isRequired,
  title: PropTypes.string, // required for all types except placeholder
  slotTitle: PropTypes.string, // only for sessions (required then)
  description: PropTypes.string,
  code: PropTypes.string,
  sessionCode: PropTypes.string, // only for sessions
  sessionId: PropTypes.number, // only for sessions
  contributionId: PropTypes.number, // only for contributions
  start: PropTypes.instanceOf(Date),
  color: entryColorSchema,
  attachmentCount: PropTypes.number,
  displayOrder: PropTypes.number,
  parentId: PropTypes.string, // only for contributions
  columnId: PropTypes.number, // set only if parentId is null
  isPoster: PropTypes.bool, // only for contributions
});

const getEntries = state => [...state.blocks, ...state.children, ...state.unscheduled];
export const hasContributions = (block, contribs) => contribs.some(e => e.parentId === block.id);
export const isChildOf = (contrib, block) => contrib.parentId === block.id;
export const getEndDt = entry => new Date(entry.start.getTime() + entry.duration * 60000);
export const isConcurrent = (entry, other) =>
  entry.id !== other.id && entry.start < getEndDt(other) && getEndDt(entry) > other.start;
export const getConcurrentEntries = (entry, entries) => entries.filter(e => isConcurrent(entry, e));
export const getLatestEntry = entries =>
  entries.reduce((acc, e) => (getEndDt(e) > getEndDt(acc) ? e : acc), entries[0]);
export const getLatestEndDt = entries => entries.length > 0 && getEndDt(getLatestEntry(entries));

/**
 * Generates the error message to be displayed in the toolbar
 * @param title Title of the error message
 * @param content Content of the error message
 * @returns {object} {error} Error message object
 */
export const displayError = (title, content) => ({error: {title, content}});

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
 * Merges the changes in the changes array onto a single change list.
 * @param {object} state State of the timetable
 * @returns {array} Merged changes as an object of the change, old entry and updated entry
 */
export const mergeChanges = ({changes, currentChangeIdx}, sessions) => {
  const mergedChanges = {};
  for (const change of changes.slice(0, currentChangeIdx)) {
    for (const [id, newValues] of Object.entries(change)) {
      if (id in mergedChanges) {
        const oldValues = mergedChanges[id];
        const old = {id, ...oldValues.old};
        const new_ = {...oldValues.change, ...newValues.new};
        mergedChanges[id] = {
          old,
          new: {...old, ...new_},
          change: _.pickBy(new_, (value, key) => !_.isEqual(key in old ? old[key] : null, value)),
        };
      } else {
        const {new: new_} = newValues;
        const old = appendSessionAttributes([newValues.old], sessions)[0];
        mergedChanges[id] = {old, new: {...old, ...new_}, change: new_};
      }
    }
  }
  return _.pickBy(mergedChanges, c => Object.keys(c.change).length > 0);
};

/**
 * Applies the changes from a changes array to the timetable's entries
 * @param {object} state State of the timetable
 * @param {array} change Change to be applied
 * @returns {object} {blocks, children} Updated blocks and child-entries
 */
const applyChange = (state, change) => {
  const newEntries = updateEntries(getEntries(state), change);
  const [scheduled, unscheduled] = _.partition(newEntries, 'start');
  const [children, blocks] = _.partition(scheduled, 'parentId');
  return {blocks, children, unscheduled: unscheduled.filter(e => e.type === 'contribution')};
};

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
  error: null,
});

/**
 * Resolves any block conflicts (parallel top-level entries in the same column) by recursively
 * shifting all conflicting blocks with left-empty-space to the left, or otherwise to the right.
 * Child-entries are left untouched. Expects all blocks to have an assigned column.
 * @param {object} state State of the timetable
 * @param {object} draggedEntries Entries which were subject to the move/resize event, if applicable
 * @param {array} change Previous change
 * @param {number} recursionCount Recursion count
 * @returns {array} Updated changes array
 */
const resolveBlockConflicts = (state, draggedEntries = null, change = [], recursionCount = 0) => {
  const blocks = updateEntries(state.blocks, change);
  const conflictingBlock = blocks.find(
    block =>
      !draggedEntries?.ids.includes(block.id) && // we avoid moving the dragged entries
      getConcurrentEntries(block, blocks).some(b => b.columnId === block.columnId)
  );
  if (!conflictingBlock) {
    return change;
  }
  if (recursionCount > blocks.length) {
    console.error(
      'resolveBlockConflicts: recursion limit exceeded',
      blocks.filter(block =>
        getConcurrentEntries(block, blocks).some(b => b.columnId === block.columnId)
      )
    );
    return change;
  }
  const {id, columnId} = conflictingBlock;
  const shift =
    columnId > 1 &&
    !getConcurrentEntries(conflictingBlock, blocks).some(b => b.columnId === columnId - 1)
      ? -1
      : 1;
  const newChange = updateEntries(change, [{id, columnId: columnId + shift}]);
  return resolveBlockConflicts(state, draggedEntries, newChange, recursionCount + 1);
};

/**
 * Removes any empty columns between parallel blocks (top-level entries) by recursively shifting all
 * blocks with left-empty-space to the left. Child-entries are left untouched. Expects all blocks to
 * have an assigned column.
 * @param {object} state State of the timetable
 * @param {array} ignoreIds Ids of the blocks to ignore
 * @param {array} change Previous change
 * @param {number} recursionCount Recursion count
 * @returns {array} Updated changes array
 */
const removeBlockGaps = (state, ignoreIds = [], change = [], recursionCount = 0) => {
  const blocks = updateEntries(state.blocks, change);
  const leftGapBlocks = blocks.filter(
    block =>
      block.columnId > 1 &&
      !ignoreIds.includes(block.id) &&
      !getConcurrentEntries(block, blocks).some(
        b => b.columnId === block.columnId - 1 && !ignoreIds.includes(b.id)
      )
  );
  if (leftGapBlocks.length === 0) {
    return change;
  }
  if (recursionCount > blocks.length) {
    console.error('removeBlockGaps: recursion limit exceeded', leftGapBlocks);
    return change;
  }
  const newChange = updateEntries(
    change,
    leftGapBlocks.map(b => ({id: b.id, columnId: b.columnId - 1}))
  );
  return removeBlockGaps(state, ignoreIds, newChange, recursionCount + 1);
};

/**
 * Performs the update of the timetable's state after a move/resize event.
 * Optionally sort the entries onto the correct columns, resolves block conflicts,
 * and removes any gaps between blocks.
 * @param {object} state State of the timetable
 * @param {array} change Change to be applied
 * @param {boolean} removeGaps Whether to remove gaps between blocks
 * @param {boolean} resolveConflicts Whether to resolve conflicts between blocks
 * @param {object} draggedEntries {ids, targetColumnId} Entries which were subject a the move/resize event, if applicable
 * @returns {object} Updated state
 */
export const updateState = (
  state,
  change,
  removeGaps = false,
  resolveConflicts = false,
  draggedEntries = null
) => {
  const newState = {...state, ...(change.length > 0 ? applyChange(state, change) : {})};
  const _makeChange = newChange => {
    change = updateEntries(change, newChange);
    newState.blocks = updateEntries(newState.blocks, newChange);
  };

  if (resolveConflicts) {
    // if the dragged entries are blocks we do a pre-layout of the blocks
    if (draggedEntries && newState.blocks.some(({id}) => draggedEntries.ids.includes(id))) {
      _makeChange(removeBlockGaps(newState, draggedEntries.ids));
    }
    // make sure all blocks have the correct column ID
    _makeChange(
      newState.blocks.flatMap(block => {
        if (!draggedEntries) {
          return block.columnId
            ? []
            : [{id: block.id, columnId: getColumnId(block, newState.blocks)}];
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
    _makeChange(resolveBlockConflicts(newState, draggedEntries));
  }
  if (removeGaps) {
    _makeChange(removeBlockGaps(newState));
  }
  const oldEntries = getEntries(state);
  const changeMap = change.flatMap(c => {
    const old = oldEntries.find(e => e.id === c.id);
    const new_ = _.pickBy(c, (value, key) => key !== 'id' && !_.isEqual(value, old[key]));
    return Object.keys(new_).length > 0 ? [[c.id, {old, new: new_}]] : [];
  });
  return changeMap.length > 0 ? addNewChange(newState, Object.fromEntries(changeMap)) : state;
};

// TODO remove
// eslint-disable-next-line no-alert
export const handleUnimplemented = () => alert('desole, ça marche pas encore :(');
