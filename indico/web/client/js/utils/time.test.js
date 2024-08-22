// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {timeStrToInt, toString} from './time';

describe('timeStrToInt', () => {
  test.each([
    ['06:00', 6 * 60],
    ['7:00', 7 * 60],
    ['19:00', 19 * 60],
    ['1200', 12 * 60],
    ['900', 9 * 60],
    ['06:02', 6 * 60 + 2],
    ['7:14', 7 * 60 + 14],
    ['1259', 12 * 60 + 59],
    ['924', 9 * 60 + 24],
  ])('should parse string like %s into integer like %s', (input, expected) => {
    const actual = timeStrToInt(input);
    expect(actual).toBe(expected);
  });

  test.each([['99:99'], ['12'], ['a'], ['3:60'], ['24:12'], ['']])(
    'should return undefined for invalid time string like %s',
    input => {
      const actual = timeStrToInt(input);
      expect(actual).toBeUndefined();
    }
  );
});

describe('toString', () => {
  test.each([[0, '00:00'], [1, '00:01'], [12 * 60 + 12, '12:12'], [23 * 60 + 59, '23:59']])(
    'should convert integer like %s to HH:MM time like %s',
    (input, expected) => {
      const actual = toString(input);
      expect(actual).toBe(expected);
    }
  );
});
