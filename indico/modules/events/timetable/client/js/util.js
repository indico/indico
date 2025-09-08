// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

/**
 * Appends the corresponding session's attributes to each entry in the array.
 * @param {array} entries Entries array
 * @param {Map} sessions Sessions map
 * @returns {array} Entries array with color attribute
 */
export const appendSessionAttributes = (entries, sessions) => {
  return entries.map(e =>
    e.sessionId ? {...e, ..._.pick(sessions[e.sessionId], ['colors', 'isPoster'])} : e
  );
};
