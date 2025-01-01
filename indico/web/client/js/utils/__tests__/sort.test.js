// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {natSortCompare} from '../sort';

describe('Natural sort', () => {
  it('should correctly compare strings containing digits', () => {
    const testCases = [
      ['Event', 'Event', 0],
      ['Event A', 'Event B', -1],
      ['Event 1', 'Event 2', -1],
      ['Event 10', 'Event 2', 1],
      ['10 Event', '2 Event', 1],
      ['2 Category', '10 Event', -1],
      ['10 Event 10', '10 Event', 1],
      ['Event 02', 'Event 2', 0],
    ];

    for (const [a, b, result] of testCases) {
      expect(natSortCompare(a, b)).toEqual(result);
    }
  });
});
