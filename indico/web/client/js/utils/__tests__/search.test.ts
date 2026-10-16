// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {normalizeSearchText} from '../search';

describe('normalizeSearchText', () => {
  it.each([
    ['Science-Lab', 'sciencelab'],
    ['Science—Lab', 'sciencelab'],
    ['Science/Lab', 'sciencelab'],
    ['  Science\t Lab\n', 'sciencelab'],
    ['-./#', ''],
    ['', ''],
  ])('normalizes %j to %j', (value, expected) => {
    expect(normalizeSearchText(value)).toBe(expected);
  });
});
