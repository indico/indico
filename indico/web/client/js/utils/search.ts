// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

export function normalizeSearchText(value: string): string {
  return _.deburr(value)
    .toLowerCase()
    .replace(/[\p{P}\s]/gu, '');
}
