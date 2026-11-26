// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {mount} from 'enzyme';
import React from 'react';

import DrillDownView from '../DrillDownView';

it('does not offer a second selection action for a disabled empty category', () => {
  const navigateTo = jest.fn();
  const focusSearch = jest.fn();
  const wrapper = mount(
    <DrillDownView
      navigatorState={{
        currentCategory: {id: 1, title: 'Current', parent_path: [{id: 0, title: 'Root'}]},
        subcategories: [],
        navigateTo,
      }}
      actionButtonText="Select"
      isNavigation={false}
      actionOn={{categories: {disabled: true, ids: [1]}}}
      emptyCategoryText="No subcategories"
      onAction={jest.fn()}
      focusSearch={focusSearch}
    />
  );

  expect(wrapper.find('button.category-action-button').prop('disabled')).toBe(true);
  const actions = wrapper.find('.placeholder-actions button');
  expect(actions.map(button => button.text())).toEqual(['navigate up', 'search']);
  actions.at(0).simulate('click');
  actions.at(1).simulate('click');
  expect(navigateTo).toHaveBeenCalledWith(0);
  expect(focusSearch).toHaveBeenCalled();
});

it('keeps the empty-category action available', () => {
  const currentCategory = {id: 1, title: 'Current', parent_path: []};
  const onAction = jest.fn();
  const wrapper = mount(
    <DrillDownView
      navigatorState={{currentCategory, subcategories: [], navigateTo: jest.fn()}}
      actionButtonText="Select"
      isNavigation={false}
      actionOn={{}}
      emptyCategoryText="No subcategories"
      onAction={onAction}
      focusSearch={jest.fn()}
    />
  );

  const action = wrapper.find('.placeholder-actions button');
  expect(action.text()).toBe('select');
  action.simulate('click');
  expect(onAction).toHaveBeenCalledWith(currentCategory);
});

it('shows a spinner instead of the empty-category text while children load', () => {
  const wrapper = mount(
    <DrillDownView
      navigatorState={{
        currentCategory: {id: 1, title: 'Current', parent_path: []},
        subcategories: [],
        navigateTo: jest.fn(),
        isLoadingSubcategories: true,
      }}
      actionButtonText="Select"
      isNavigation={false}
      actionOn={{}}
      emptyCategoryText="No subcategories"
      onAction={jest.fn()}
      focusSearch={jest.fn()}
    />
  );

  expect(wrapper.find('.i-spinner').exists()).toBe(true);
  expect(wrapper.text()).not.toContain('No subcategories');
});
