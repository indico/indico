// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

function smartCamelCase(string) {
  return _.camelCase(string).replace(/Url/g, 'URL');
}

export function camelizeKeys(obj) {
  if (!_.isPlainObject(obj) && !_.isArray(obj)) {
    return obj;
  }

  if (_.isArray(obj)) {
    return obj.map(camelizeKeys);
  }

  return Object.entries(obj).reduce((accum, [key, value]) => {
    if (key.match(/^[A-Za-z_]+$/)) {
      return {...accum, [smartCamelCase(key)]: camelizeKeys(value)};
    } else {
      return {...accum, [key]: camelizeKeys(value)};
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
