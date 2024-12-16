// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
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

/**
 * Create a selection object
 *
 * The object is immutable, and each operation creates a new
 * copy.
 */
export function newSelection(left, right, trigger, leftLocked, rightLocked) {
  return Object.freeze({
    left,
    right,
    trigger,
    leftLocked,
    rightLocked,

    get unlocked() {
      console.log(leftLocked, rightLocked);
      return !leftLocked && !rightLocked;
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
      return newSelection(newLeft, newRight, newTrigger, leftLocked, rightLocked);
    },

    toDateRange() {
      return new DateRange(left, right);
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
  if (!selection.trigger) {
    return;
  }

  const close = updatedSelection => ({selection: updatedSelection, close: true});
  const keepOpen = updatedSelection => ({selection: updatedSelection, close: false});
  const selectionState = selection.getSelectionState();

  switch (true) {
    case selection.unlocked:
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
      }
      break;
    case selection.leftLocked:
      return close(selection.copy({right: date, trigger: RIGHT}));
    case selection.rightLocked:
      return close(selection.copy({left: date, trigger: LEFT}));
    default:
      console.warn(`Invalid lock state ${selection.leftLocked}, ${selection.rightLocked}`);
      return keepOpen(selection);
  }
}
