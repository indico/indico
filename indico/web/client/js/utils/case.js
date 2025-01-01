// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

function smartCamelCase(string) {
  return _.camelCase(string).replace(/Url/g, 'URL');
}

/**
 * Camelizes keys of an object recursively.
 *
 * @param {Object} obj - Object to camelize
 * @param {string|null} skip - Key of object to skip
 */
export function camelizeKeys(obj, skip = null) {
  if (!_.isPlainObject(obj) && !_.isArray(obj)) {
    return obj;
  }

  if (_.isArray(obj)) {
    return obj.map(x => camelizeKeys(x, skip));
  }

  return Object.entries(obj).reduce((accum, [key, value]) => {
    if (skip && skip === key) {
      return {...accum, [smartCamelCase(key)]: value};
    } else if (key.match(/^[A-Za-z_]+$/)) {
      return {...accum, [smartCamelCase(key)]: camelizeKeys(value, skip)};
    } else {
      return {...accum, [key]: camelizeKeys(value, skip)};
    }
  }, {});
}

export function snakifyKeys(obj) {
  if (!_.isPlainObject(obj) && !_.isArray(obj)) {
    return obj;
  }

  if (_.isArray(obj)) {
    return obj.map(snakifyKeys);
  }

  return Object.entries(obj).reduce((accum, [key, value]) => {
    if (key.match(/^[A-Za-z_]+$/)) {
      return {...accum, [_.snakeCase(key)]: snakifyKeys(value)};
    } else {
      return {...accum, [key]: snakifyKeys(value)};
    }
  }, {});
}
