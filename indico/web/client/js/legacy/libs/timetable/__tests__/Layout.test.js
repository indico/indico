// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fs from 'fs';
import path from 'path';

import _ from 'underscore';

// The legacy timetable code consists of plain scripts defining globals, so we
// evaluate them in the global scope instead of importing them as modules.
const loadLegacyScript = relPath => {
  const source = fs.readFileSync(path.resolve(__dirname, '../..', relPath), 'utf8');
  // eslint-disable-next-line no-eval
  (0, eval)(source);
};

beforeAll(() => {
  window._ = _;
  window.zeropad = number => (number < 10 ? `0${number}` : `${number}`);
  window.$L = list => ({indexOf: item => (list.includes(item) ? list.indexOf(item) : null)});
  window.SortCriteria = {
    Integer: (a, b) => (a === b ? 0 : a < b ? -1 : 1),
  };
  window.TimetableDefaults = {
    resolution: 1,
    wholeDay: 7,
    layouts: {
      compact: {values: {pxPerHour: 150, pxPerSpace: 2, minPxPerBlock: 50}},
    },
  };
  [
    'presentation/Core/Primitives.js',
    'presentation/Core/Iterators.js',
    'presentation/Core/Tools.js',
    'presentation/Core/String.js',
    'presentation/Core/Type.js',
    'presentation/Ui/Text.js',
    'timetable/Layout.js',
  ].forEach(loadLegacyScript);
});

describe('CompactLayoutManager', () => {
  it('keeps contributions of parallel session slots in their columns', () => {
    // Four parallel blocks of the same session with four consecutive 15-minute
    // contributions each, as used in the detailed timetable view where session
    // blocks are flattened into their contributions
    const slots = {
      1240: [5670, 5684, 5685, 5669],
      1244: [6343, 5615, 5674, 5616],
      1245: [5680, 5681, 5683, 5976],
      1268: [5981, 5673, 5667, 5672],
    };
    const times = ['10:30', '10:45', '11:00', '11:15', '11:30'];
    const data = {};
    Object.entries(slots).forEach(([slotId, contribIds]) => {
      contribIds.forEach((contribId, i) => {
        data[`c${contribId}`] = {
          sessionId: 772,
          sessionSlotId: +slotId,
          startDate: {time: `${times[i]}:00`},
          endDate: {time: `${times[i + 1]}:00`},
        };
      });
    });

    const [, , blocks] = new window.CompactLayoutManager().drawDay(
      data,
      'session',
      null,
      null,
      false
    );

    Object.entries(slots).forEach(([slotId, contribIds]) => {
      const columns = contribIds.map(contribId => blocks[`c${contribId}`].assigned);
      expect({slotId, columns: new Set(columns).size}).toEqual({slotId, columns: 1});
    });
  });
});
