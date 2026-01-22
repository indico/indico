// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/**
 * Checks if a category action should be disabled
 * @param {Object} category - The category to check
 * @param {Function} shouldDisableAction - Function that returns a reason string if disabled, or falsy if allowed
 * @returns {Object} { disabled: boolean, message: string|null }
 */
export function getCategoryActionState(category, shouldDisableAction) {
  if (!shouldDisableAction) {
    return {disabled: false, message: null};
  }

  const reason = shouldDisableAction(category);
  if (reason) {
    return {disabled: true, message: reason};
  }

  return {disabled: false, message: null};
}
