// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _slugify from 'slugify';

function trim(value) {
  return typeof value === 'string' ? value.trim() : value;
}

function slugify(value) {
  return typeof value === 'string' ? _slugify(value, {lower: true}) : value;
}

export default {
  trim,
  slugify,
};
