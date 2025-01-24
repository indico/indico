// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// This module implements the date selection algorithm for
// the date range picker.

import {DateRange} from 'indico/utils/date';

/**
 * Represents a selection of dates in a range date picker
 *
 * This model provides an abstract representation of the date
 * selection workflow. The rules related to date selection
 * (except for selection validity) is expressed by the functions
 * in this module. Therefore, changes relating to the selection
 * rules should be made in this class (specifically in the
 * `select()` function).
 *
 * Call `triggerLeft()` or `triggerRight()` to signal that
 * the user is targeting a specific side of the range. These
 * methods are called without any arguments.
 *
 * Call `select(Selection, Date)` to apply the selection.
 *
 * The resulting selection can be retrieved as a `DateRange`
 * object by calling `toDateRange()` method on the Selection
 * object.
 */

export const LEFT = 'L';
export const RIGHT = 'R';
export const NONE = 'N';
export const LEFT_ONLY = 'L';
export const RIGHT_ONLY = 'R';
export const BOTH = 'B';
export const CLOSE = true;

const close = updatedSelection => ({selection: updatedSelection, close: true});
const keepOpen = updatedSelection => ({selection: updatedSelection, close: false});

export const SELECTION_RANGE_WITH_TRIGGERS = 'rangeWithTriggers';
export const SELECTION_SIMPLE_RANGE = 'simpleRange';
export const SELECTION_SINGLE = 'single';
const SELECTION_DEFAULT_STRATEGY = SELECTION_RANGE_WITH_TRIGGERS;
const SELECTION_STRATEGIES = {
  [SELECTION_RANGE_WITH_TRIGGERS]: (selection, date) => {
    if (!selection.trigger) {
      return {selection, close: true};
    }

    const selectionState = selection.getSelectionState();

    if (selection.unlocked) {
      // No selection -> select left
      if (selectionState === NONE) {
        return keepOpen(selection.copy({left: date, trigger: RIGHT}));
      }

      switch (selectionState + selection.trigger) {
        case 'LL':
          return keepOpen(selection.copy({left: date, trigger: RIGHT}));
        case 'RR':
          if (date > selection.right) {
            return keepOpen(selection.copy({left: date, right: null}));
          }
          return close(selection.copy({right: date}));
        case 'LR':
          if (date < selection.left) {
            return keepOpen(selection.copy({left: date}));
          }
          return close(selection.copy({right: date}));
        case 'RL':
          if (date > selection.right) {
            return keepOpen(selection.copy({left: date, right: null}));
          }
          return close(selection.copy({left: date}));
        case 'BL':
          if (date > selection.right) {
            return keepOpen(selection.copy({left: date, right: null, trigger: RIGHT}));
          }
          return keepOpen(selection.copy({left: date, trigger: RIGHT}));
        case 'BR':
          if (date < selection.left) {
            return keepOpen(selection.copy({left: date, right: null}));
          }
          return close(selection.copy({right: date}));
        default:
          console.warn(`Invalid state-trigger combination ${selectionState + selection.trigger}`);
          return keepOpen(selection);
      }
    }

    if (selection.leftLocked) {
      return close(selection.copy({right: date, trigger: RIGHT}));
    }

    if (selection.rightLocked) {
      return close(selection.copy({left: date, trigger: LEFT}));
    }

    console.warn(`Invalid lock state ${selection.leftLocked}, ${selection.rightLocked}`);
    return keepOpen(selection);
  },
  [SELECTION_SIMPLE_RANGE]: (selection, date) => {
    const selectionState = selection.getSelectionState();
    switch (selectionState) {
      case NONE:
        return keepOpen(selection.copy({left: date}));
      case LEFT_ONLY:
        if (selection.left > date) {
          return close(selection.copy({left: date, right: selection.left}));
        } else {
          return close(selection.copy({right: date}));
        }
      case RIGHT_ONLY:
        if (selection.right < date) {
          return close(selection.copy({right: date, left: selection.right}));
        } else {
          return close(selection.copy({left: date}));
        }
      case BOTH:
        return keepOpen(selection.copy({left: date, right: null}));
      default:
        throw Error(
          `simple range selection: selection.getSelectionState() returned invalid state ${selectionState}`
        );
    }
  },
  [SELECTION_SINGLE]: (selection, date) => {
    return close(selection.copy({date}));
  },
};

/**
 * Create a selection object
 *
 * The object is immutable, and each operation creates a new
 * copy.
 */
export function newRangeSelection(
  left,
  right,
  trigger,
  leftLocked,
  rightLocked,
  type = SELECTION_DEFAULT_STRATEGY
) {
  return Object.freeze({
    left,
    right,
    trigger,
    leftLocked,
    rightLocked,
    type,

    get unlocked() {
      return !leftLocked && !rightLocked;
    },

    get completed() {
      return this.getSelectionState() === BOTH;
    },

    getSelectionState() {
      if (!left && !right) {
        return NONE;
      }
      if (left && right) {
        return BOTH;
      }
      if (left) {
        return LEFT_ONLY;
      }
      return RIGHT_ONLY;
    },

    copy({left: newLeft = left, right: newRight = right, trigger: newTrigger = trigger} = {}) {
      return newRangeSelection(newLeft, newRight, newTrigger, leftLocked, rightLocked, type);
    },

    toDateRange() {
      return new DateRange(left, right);
    },
  });
}

export function newSingleSelection(date, locked, type = SELECTION_SINGLE) {
  return Object.freeze({
    date,
    locked,
    type,

    get unlocked() {
      return !locked;
    },

    get completed() {
      return this.getSelectionState() === BOTH;
    },

    getSelectionState() {
      return date ? BOTH : NONE;
    },

    copy({date: newDate = date, locked: newLocked = locked} = {}) {
      return newSingleSelection(newDate, newLocked, type);
    },

    toDateRange() {
      return new DateRange(date, date);
    },
  });
}

export function triggerLeft(selection) {
  if (selection.leftLocked) {
    return selection;
  }
  return selection.copy({trigger: LEFT});
}

export function triggerRight(selection) {
  if (selection.rightLocked) {
    return selection;
  }
  return selection.copy({trigger: RIGHT});
}

export function select(selection, date) {
  const selectionStrategy = SELECTION_STRATEGIES[selection.type];
  return selectionStrategy(selection, date);
}
