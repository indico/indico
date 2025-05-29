// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {timeString} from './prop_types';

describe.each([['timeString', timeString], ['timeString.isRequired', timeString.isRequired]])(
  '%s',
  (_, propType) => {
    it.each([['00:00'], ['00:01'], ['00:10'], ['01:00'], ['10:00'], ['23:59']])(
      'should not flag valid time, like %s',
      s => {
        expect(propType({s}, 's', 'Foo')).toBeUndefined();
      }
    );

    it.each([['00 : 00'], ['24:00'], ['5:12'], ['05:60'], ['05.22'], ['05h22'], ['aaa']])(
      'should flag invalid time, like %s',
      s => {
        expect(timeString({s}, 's', 'Foo')).toBeInstanceOf(Error);
      }
    );
  }
);
