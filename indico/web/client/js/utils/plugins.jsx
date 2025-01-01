// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

export const registries = new Map();

function getRegistry(name, create = false) {
  let registry = registries.get(name);
  if (registry === undefined) {
    registry = [];
    if (create) {
      registries.set(name, registry);
    }
  }
  return registry;
}

/**
 * Register an object for an entry point.
 * @param {string} plugin - the name of the plugin
 * @param {string} entryPoint - the name of the entry point
 * @param object - the object to register; can be whatever the entry point expects
 */
export function registerPluginObject(plugin, entryPoint, object) {
  const registry = getRegistry(entryPoint, true);
  registry.push({plugin, object});
}

/**
 * Return the list of objects registered for an entry point.
 * @param {string} entryPoint - the name of the entry point
 * @param {boolean} verbose - whether to return the entries with all metadata or just the objects
 */
export function getPluginObjects(entryPoint, verbose = false) {
  const registry = getRegistry(entryPoint);
  return verbose ? registry : registry.map(entry => entry.object);
}

/**
 * Register a react component for an entry point.
 * @param {string} plugin - the name of the plugin
 * @param {string} entryPoint - the name of the entry point
 * @param component - the react component
 * @param props - props that will be passed to the component when rendering it
 */
export function registerPluginComponent(plugin, entryPoint, component, props = {}) {
  registerPluginObject(plugin, entryPoint, {component, props});
}

/**
 * Render react components for an entry point.
 * @param {string} entryPoint - the name of the entry point
 * @param props - props that will be passed to the component when rendering it
 */
export function renderPluginComponents(entryPoint, props) {
  const entries = getPluginObjects(entryPoint, true);
  return entries.map(({plugin, object: {component: Component, props: pluginProps}}, i) => (
    // eslint-disable-next-line react/no-array-index-key
    <Component key={`${entryPoint}-${plugin}-${i}`} {...props} {...pluginProps} />
  ));
}
