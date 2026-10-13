// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/**
 * Checks if an action on a category is allowed according to actionOn rules.
 *
 * @param {Object} category - The category object
 * @param {Object} actionOn - Restriction configuration object
 * @returns {Object} { allowed: boolean, message: string }
 */
export function canActOnCategory(category, actionOn = {}) {
  if (!category) {
    return {allowed: true, message: ''};
  }

  // 1. Direct categories / groups match
  if (actionOn.categories?.disabled) {
    if (actionOn.categories.ids?.includes(category.id)) {
      return {allowed: false, message: actionOn.categories.message || ''};
    }
    for (const group of actionOn.categories.groups || []) {
      if (group.ids?.includes(category.id)) {
        return {allowed: false, message: group.message || ''};
      }
    }
  }

  // 2. Descending from disallowed categories
  if (actionOn.categoriesDescendingFrom?.disabled) {
    const parentPath = category.parent_path || [];
    const disallowedIds = actionOn.categoriesDescendingFrom.ids || [];
    for (let i = parentPath.length - 1; i >= 0; i--) {
      const parent = parentPath[i];
      if (disallowedIds.includes(parent.id)) {
        const msg = (actionOn.categoriesDescendingFrom.message || '').replace('{0}', parent.title);
        return {allowed: false, message: msg};
      }
    }
  }

  // 3. Categories without event creation rights
  if (actionOn.categoriesWithoutEventCreationRights?.disabled && !category.can_create_events) {
    return {
      allowed: false,
      message: actionOn.categoriesWithoutEventCreationRights.message || '',
    };
  }

  // 4. Categories without management rights
  if (actionOn.categoriesWithoutCategoryManagementRights?.disabled && !category.can_manage) {
    return {
      allowed: false,
      message: actionOn.categoriesWithoutCategoryManagementRights.message || '',
    };
  }

  // 5. Categories without event proposal rights
  if (actionOn.categoriesWithoutEventProposalRights?.disabled && !category.can_propose_events) {
    return {
      allowed: false,
      message: actionOn.categoriesWithoutEventProposalRights.message || '',
    };
  }

  // 6. Categories without event proposal or creation rights
  if (
    actionOn.categoriesWithoutEventProposalOrCreationRights?.disabled &&
    !category.can_propose_events &&
    !category.can_create_events
  ) {
    return {
      allowed: false,
      message: actionOn.categoriesWithoutEventProposalOrCreationRights.message || '',
    };
  }

  return {allowed: true, message: ''};
}
