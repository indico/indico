// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createDateParser} from './date_parser';

describe('createDateParser', () => {
  test.each([['yyy.mm.dd'], ['yyyy.mm'], ['dd/mm/'], '[d//y]'])(
    'Given an incomplete format string like %s, creating the parser will fail',
    formatString => {
      expect(() => createDateParser(formatString)).toThrow();
    }
  );

  test.each([
    ['yyyy.mm.dd', '2024.02.11'],
    ['yyyy/mm/dd', '2024/02/11'],
    ['mm/dd/yyyy', '02/11/2024'],
    ['dd.mm.yyyy.', '11.02.2024.'],
  ])(
    'Given a format string like %s, when passsed a formatted date like %s, it returns a Date object for that date',
    (formatString, formattedDate) => {
      const parse = createDateParser(formatString);
      const actual = parse(formattedDate);
      const expected = new Date(2024, 1, 11);
      expect(actual).toEqual(expected);
    }
  );

  test.each([['2/07/2024'], ['02/7/2024'], ['2/7/2024'], ['2.7.2024'], ['2-7.2024']])(
    'Given a format string mm/dd/yyyy, when passed a formatted date that does not quite match, like %s, it will still successfully parse it',
    formattedDate => {
      const formatString = 'mm/dd/yyyy';
      const parse = createDateParser(formatString);
      const actual = parse(formattedDate);
      const expected = new Date(2024, 1, 7);
      expect(actual).toEqual(expected);
    }
  );

  test.each([['2021.1.12'], ['01//12/2021'], ['13/02/2021'], ['11/65/2021'], ['1/2']])(
    'Given a formatting string mm/dd/yyyy, when passed an invalid formatted date, like %s, it will return undefined',
    formattedDate => {
      const formatString = 'mm/dd/yyyy';
      const parse = createDateParser(formatString);
      const actual = parse(formattedDate);
      expect(actual).toBeUndefined();
    }
  );

  test('Given a format string like mm/dd/yyyy, when passed a correctly formatted date that represent an invalid date, it will return undefined', () => {
    const formatString = 'mm/dd/yyyy';
    const formattedDate = '02/31/2024';
    const parse = createDateParser(formatString);
    const actual = parse(formattedDate);
    expect(actual).toBeUndefined();
  });
});
