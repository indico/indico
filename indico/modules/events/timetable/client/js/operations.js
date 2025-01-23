// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

import {Translate} from 'indico/react/i18n';

import {
  displayError,
  getConcurrentEntries,
  getEndDt,
  getLatestEndDt,
  getLatestEntry,
  isChildOf,
  isConcurrent,
  updateState,
} from './util';

/**
 * Performs the initial sorting of the entries onto the correct columns.
 * Same sorting as updateState, but saves the changes onto the blocks and children arrays directly
 * instead of polluting the changes array.
 * @param {array} blocks Blocks (top-level-entries) to be sorted
 * @param {array} children Child-entries to be sorted
 * @returns {object} {blocks, children} Sorted blocks and children
 */
export const preprocessEntries = (state, blocks, children, unscheduled) => ({
  ...state,
  blocks: updateState({...state, blocks}, [], true, true).blocks,
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
    ? state.children
        .filter(c => newBlocks.some(b => isChildOf(c, b)))
        .map(c => ({
          id: c.id,
          start: new Date(c.start.getTime() + timeDiff),
        }))
    : [];
  return updateState(state, [...newBlocks, ...newContribs], true, true, {
    ids: blocks.map(b => b.id),
    targetColumnId: columnId,
  });
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
  const {children} = state;
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
  const newEnd =
    block.isPoster || block.type === 'break' || block.type === 'contribution'
      ? end
      : new Date(
          Math.max(
            ...children.filter(c => isChildOf(c, block)).map(c => getEndDt(c).getTime()),
            end.getTime()
          )
        );
  if (
    newEnd.getTime() !== getEndDt(block).getTime() ||
    block.type === 'break' ||
    block.type === 'contribution'
  ) {
    newEntry.duration = (newEnd.getTime() - newStart.getTime()) / 60000;
  }
  if (!newEntry.start && !newEntry.duration) {
    return {};
  }
  return updateState(state, [newEntry], true, true, {ids: [block.id], targetColumnId: columnId});
};

/**
 * Rearranges contributions in a block in order to fit a new contribution
 * @param {array} rearranged Contributions to be rearranged
 * @param {array} inserted Contribution to be inserted
 * @returns {array|boolean} Rearranged contributions or false if they don't fit in the block
 */
const rearrangeContribsAfterMove = (rearranged, inserted) => {
  const prevContrib = getLatestEntry(rearranged.filter(c => getEndDt(c) <= inserted[0].start));
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
  const {blocks, children} = state;
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
    return displayError(
      Translate.string('Scheduling error'),
      Translate.string('Cannot schedule contributions inside a block from a different session.')
    );
  }
  // check if it's being dragged to outside of a block or to a block without enough space
  if (!parent) {
    return moveBlocks(state, newContribs, columnId);
  }
  // if it's being dragged to a poster session, just schedule it at the beginning with the default duration
  if (parent?.isPoster) {
    return updateState(
      state,
      newContribs.map(c => ({...c, parentId: parent.id, start: parent.start}))
    );
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
  // if the contrib used to be a block, it might have left a gap when moved
  return updateState(state, changes, !contribs[0].parentId);
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
  const {blocks, children} = state;
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
  let newParent = null;
  if (getEndDt(newContribs.at(-1)) > getEndDt(parent)) {
    newParent = {
      id: parent.id,
      duration: (getEndDt(newContribs.at(-1)).getTime() - parent.start.getTime()) / 60000,
    };
  } else if (newContribs[0].start < parent.start) {
    newParent = {id: parent.id, start: newContribs[0].start};
  }
  return newParent
    ? updateState(state, [...newContrib, newParent], true, true)
    : updateState(state, newContribs);
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
    return updateState(state, [{id: entry.id, start: null}]);
  }
  const contribs = state.children.filter(c => isChildOf(c, entry));
  return updateState(state, [...contribs, entry].map(({id}) => ({id, start: null})), true, true);
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
 * @param {Set} contribIds Contributions to be scheduled
 * @param {number} gap Gap between contributions in minutes
 * @returns {object} {changes, currentChangeIdx} Updated changes array and an incremented
 * currentChangeIdx
 */
export const scheduleContribs = (state, contribIds, gap) => {
  const {blocks, children, unscheduled} = state;
  const selectedBlock = state.selectedId && blocks.find(b => b.id === state.selectedId);
  const parent = selectedBlock?.type === 'session' ? selectedBlock : null;
  const columnId =
    selectedBlock?.columnId || blocks.reduce((acc, b) => Math.max(acc, b.columnId), 0) + 1;
  const contribs =
    contribIds.size > 0
      ? unscheduled.filter(c => contribIds.has(c.id))
      : unscheduled.filter(c => (parent ? c.sessionId === parent.sessionId : !c.sessionId));
  // TODO fix start datetime (based on selected day)
  console.debug('scheduleContribs', contribIds, contribs, gap, parent, selectedBlock, columnId);
  if (parent && !parent.isPoster) {
    const lastEndDt = getLatestEndDt(children.filter(c => isChildOf(c, parent))) || parent.start;
    if (lastEndDt.getTime() >= getEndDt(parent).getTime()) {
      // TODO expand the session to fit the new contribs
      return resizeBlock(state, {
        event: parent,
        start: parent.start,
        end: new Date(lastEndDt.getTime() + gap * 60000),
      });
    }
    return moveContribs(state, contribs, lastEndDt, columnId, gap);
  }
  const start =
    (parent?.isPoster && parent.start) ||
    (selectedBlock && getEndDt(selectedBlock)) ||
    getLatestEndDt(blocks.filter());
  return moveContribs(state, contribs, start, columnId, gap);
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
  return updateState(
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
