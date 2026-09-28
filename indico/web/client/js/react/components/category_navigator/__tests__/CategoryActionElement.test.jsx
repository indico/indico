// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {mount} from 'enzyme';
import React from 'react';

import CategoryActionElement from '../CategoryActionElement';

describe('CategoryActionElement', () => {
  const category = {
    id: 123,
    title: 'Physics Department',
  };

  it('renders an anchor tag when isNavigation is true and actionUrl is provided', () => {
    const wrapper = mount(
      <CategoryActionElement
        category={category}
        actionButtonText="Navigate to"
        isNavigation
        actionUrl={cat => `/category/${cat.id}`}
      />
    );

    const anchor = wrapper.find('a.category-action-button');
    expect(anchor).toHaveLength(1);
    expect(anchor.prop('href')).toBe('/category/123');
    expect(anchor.text()).toBe('Navigate to\u00a0Physics Department');
    expect(anchor.find('.visually-hidden').text()).toBe('\u00a0Physics Department');
  });

  it('leaves navigation to the link instead of also calling onAction', () => {
    const onAction = jest.fn();
    const wrapper = mount(
      <CategoryActionElement
        category={category}
        actionButtonText="Navigate to"
        isNavigation
        actionUrl={cat => `/category/${cat.id}`}
        onAction={onAction}
      />
    );

    wrapper.find('a.category-action-button').simulate('click');
    expect(onAction).not.toHaveBeenCalled();
  });

  it('renders a button when isNavigation is false', () => {
    const onAction = jest.fn();
    const wrapper = mount(
      <CategoryActionElement
        category={category}
        actionButtonText="Select"
        isNavigation={false}
        onAction={onAction}
      />
    );

    const button = wrapper.find('button.category-action-button');
    expect(button).toHaveLength(1);
    expect(button.prop('type')).toBe('button');
    expect(button.text()).toContain('Select');
    expect(button.find('.visually-hidden').text()).toBe('\u00a0Physics Department');

    button.simulate('click');
    expect(onAction).toHaveBeenCalledWith(category);
  });

  it('renders disabled button with tooltip when disabled is true', () => {
    const wrapper = mount(
      <CategoryActionElement
        category={category}
        actionButtonText="Select"
        disabled
        disabledMessage="You cannot select this category"
      />
    );

    const tooltip = wrapper.find('ind-with-tooltip');
    expect(tooltip).toHaveLength(1);
    expect(tooltip.find('span[data-tip-content]').text()).toBe('You cannot select this category');

    const button = wrapper.find('button.category-action-button.disabled');
    expect(button).toHaveLength(1);
    expect(button.prop('disabled')).toBe(true);
  });
});
