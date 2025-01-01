// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/**
 * Unordered attachable collection.
 */
type('Bag', ['EnumerableAttachable'], {}, function() {
  var counter = 0;
  var items = {};
  // IE enumeration safe
  var pendingItems = null;

  function getDetach(id) {
    return function detach() {
      if (id in items) {
        delete items[id];
        return true;
      }
      return false;
    };
  }
  this.each = function(iterator) {
    pendingItems = {};
    var result = enumerate(items, iterator);
    extend(items, pendingItems);
    pendingItems = null;
    return result;
  };

  // defers set if enumerating (for IE)
  this.attach = function(item) {
    var id = counter++;
    if (exists(pendingItems)) {
      pendingItems[id] = item;
    } else {
      items[id] = item;
    }
    return getDetach(id);
  };
});
