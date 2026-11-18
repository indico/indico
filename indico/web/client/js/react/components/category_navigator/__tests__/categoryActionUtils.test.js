// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {canActOnCategory} from '../categoryActionUtils';

describe('canActOnCategory', () => {
  const baseCategory = {
    id: 42,
    title: 'Test Category',
    can_create_events: true,
    can_manage: true,
    has_children: false,
    parent_path: [{id: 1, title: 'Root Category'}],
  };

  it('allows category when actionOn is empty', () => {
    expect(canActOnCategory(baseCategory, {})).toEqual({allowed: true, message: ''});
    expect(canActOnCategory(null)).toEqual({allowed: true, message: ''});
  });

  it('disables category matching direct id in actionOn.categories', () => {
    const actionOn = {
      categories: {
        disabled: true,
        ids: [42],
        message: 'Cannot select this category',
      },
    };
    expect(canActOnCategory(baseCategory, actionOn)).toEqual({
      allowed: false,
      message: 'Cannot select this category',
    });
  });

  it('disables category matching a group in actionOn.categories', () => {
    const actionOn = {
      categories: {
        disabled: true,
        groups: [
          {
            ids: [42],
            message: 'Category is in restricted group',
          },
        ],
      },
    };
    expect(canActOnCategory(baseCategory, actionOn)).toEqual({
      allowed: false,
      message: 'Category is in restricted group',
    });
  });

  it('disables category descending from a disallowed parent', () => {
    const actionOn = {
      categoriesDescendingFrom: {
        disabled: true,
        ids: [1],
        message: 'Cannot select categories inside {0}',
      },
    };
    expect(canActOnCategory(baseCategory, actionOn)).toEqual({
      allowed: false,
      message: 'Cannot select categories inside Root Category',
    });
  });

  it('disables category without event creation rights', () => {
    const actionOn = {
      categoriesWithoutEventCreationRights: {
        disabled: true,
        message: 'No event creation rights',
      },
    };
    const restrictedCategory = {...baseCategory, can_create_events: false};
    expect(canActOnCategory(restrictedCategory, actionOn)).toEqual({
      allowed: false,
      message: 'No event creation rights',
    });
    expect(canActOnCategory(baseCategory, actionOn)).toEqual({
      allowed: true,
      message: '',
    });
  });

  it('disables category without management rights', () => {
    const actionOn = {
      categoriesWithoutCategoryManagementRights: {
        disabled: true,
        message: 'No management rights',
      },
    };
    const restrictedCategory = {...baseCategory, can_manage: false};
    expect(canActOnCategory(restrictedCategory, actionOn)).toEqual({
      allowed: false,
      message: 'No management rights',
    });
  });

  it('disables category without event proposal rights', () => {
    const actionOn = {
      categoriesWithoutEventProposalRights: {
        disabled: true,
        message: 'No event proposal rights',
      },
    };
    const restrictedCategory = {...baseCategory, can_propose_events: false};
    expect(canActOnCategory(restrictedCategory, actionOn)).toEqual({
      allowed: false,
      message: 'No event proposal rights',
    });
  });

  it('disables category without event proposal or creation rights', () => {
    const actionOn = {
      categoriesWithoutEventProposalOrCreationRights: {
        disabled: true,
        message: 'No event proposal or creation rights',
      },
    };
    const restrictedCategory = {
      ...baseCategory,
      can_propose_events: false,
      can_create_events: false,
    };
    expect(canActOnCategory(restrictedCategory, actionOn)).toEqual({
      allowed: false,
      message: 'No event proposal or creation rights',
    });
    const withCreateRights = {
      ...baseCategory,
      can_propose_events: false,
      can_create_events: true,
    };
    expect(canActOnCategory(withCreateRights, actionOn)).toEqual({
      allowed: true,
      message: '',
    });
  });
});
