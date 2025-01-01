// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/**
 * Creates a watch value and binds it to the source.
 * @param {Object} source
 * @param {Function} template
 * @return {WatchValue}
 */
function $V(source, template) {
  return bind.toAccessor(new WatchValue(), source, template);
}

/**
 * Observable value.
 */
type(
  'WatchValue',
  ['WatchAccessor'],
  {},
  /**
   * Initializes a new watch value with the given value.
   * @param {Object} value
   */
  function(value) {
    var valueObservers = commands();
    this.WatchAccessor(
      function() {
        return value;
      },
      function(newValue) {
        if (!equals(value, newValue)) {
          var oldValue = value;
          value = newValue;
          valueObservers(newValue, oldValue);
        }
      },
      valueObservers.attach,
      function(observer) {
        return observer(value, value);
      }
    );
  }
);

type(
  'WatchPair',
  ['WatchValue'],
  {
    key: null,
  },
  function(key, value) {
    this.key = key;
    this.WatchValue(value);
  }
);
