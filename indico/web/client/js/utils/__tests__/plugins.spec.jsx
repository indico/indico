// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {mount} from 'enzyme';
import React from 'react';

import {
  registerPluginObject,
  getPluginObjects,
  registerPluginComponent,
  renderPluginComponents,
  registries,
} from '../plugins';

afterEach(() => {
  registries.clear();
});

describe('Plugin object registry', () => {
  it('works with nothing registered', () => {
    expect(getPluginObjects('foo')).toEqual([]);
    expect(getPluginObjects('foo', true)).toEqual([]);
  });

  it('registers an object and retrieves it', () => {
    const plugin = 'bar';
    const object = {hello: 'world'};
    registerPluginObject(plugin, 'foo', object);
    expect(getPluginObjects('foo')).toEqual([object]);
    expect(getPluginObjects('foo', true)).toEqual([{plugin, object}]);
  });

  it('returns multiple objects', () => {
    const plugin = 'bar';
    registerPluginObject(plugin, 'foo', 1);
    registerPluginObject(plugin, 'foo', 2);
    expect(getPluginObjects('foo')).toEqual([1, 2]);
    expect(getPluginObjects('foo', true)).toEqual([{plugin, object: 1}, {plugin, object: 2}]);
  });
});

describe('Plugin component registry', () => {
  it('works with nothing registered', () => {
    expect(renderPluginComponents('foo')).toEqual([]);
    expect(renderPluginComponents('foo', true)).toEqual([]);
  });

  it('register a component and renders it', () => {
    const plugin = 'bar';
    const MyComponent = () => `test`;
    const MyOtherComponent = () => `asdf`;
    registerPluginComponent(plugin, 'foo', MyComponent);
    // single component
    let mounted = mount(<div>{renderPluginComponents('foo')}</div>);
    expect(mounted.children().props()).toEqual({});
    // same component twice
    registerPluginComponent(plugin, 'foo', MyComponent);
    mounted = mount(<div>{renderPluginComponents('foo')}</div>);
    expect(mounted.children().map(c => c.props())).toEqual([{}, {}]);
    // another component
    registerPluginComponent(plugin, 'foo', MyOtherComponent);
    mounted = mount(<div>{renderPluginComponents('foo')}</div>);
    expect(mounted.children().map(c => c.name())).toEqual([
      'MyComponent',
      'MyComponent',
      'MyOtherComponent',
    ]);
    expect(mounted.children().map(c => c.props())).toEqual([{}, {}, {}]);
    expect(mounted.children().map(c => c.text())).toEqual(['test', 'test', 'asdf']);
  });

  it('passes props provided during registration and execution time', () => {
    const plugin = 'bar';
    const MyComponent = () => `test`;
    const MyOtherComponent = () => `asdf`;
    registerPluginComponent(plugin, 'foo', MyComponent);
    // single component
    let mounted = mount(<div>{renderPluginComponents('foo')}</div>);
    expect(mounted.children().props()).toEqual({});
    // another component
    registerPluginComponent(plugin, 'foo', MyOtherComponent, {reg: 'foo', other: 'bar'});
    mounted = mount(<div>{renderPluginComponents('foo')}</div>);
    expect(mounted.children().map(c => c.props())).toEqual([{}, {reg: 'foo', other: 'bar'}]);
    // same prop in both places -> the one during registration wins
    mounted = mount(<div>{renderPluginComponents('foo', {other: 'test'})}</div>);
    expect(mounted.children().map(c => c.props())).toEqual([
      {other: 'test'},
      {reg: 'foo', other: 'bar'},
    ]);
    expect(mounted.children().map(c => c.text())).toEqual(['test', 'asdf']);
  });
});
