// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/**
 * Truncates a category path if it is too long.
 */
Util.truncateCategPath = function(list) {
  var first = list.slice(0, 1);
  var last = list.length > 1 ? list.slice(-1) : [];
  list = list.slice(1, -1);

  var truncated = false;

  var chars = list.join('');
  while (chars.length > 10) {
    truncated = true;
    list = list.slice(1);
    chars = list.join('');
  }

  if (truncated) {
    list = concat(['...'], list);
  }

  return translate(concat(first, list, last), function(val) {
    return escapeHTML(val);
  });
};
