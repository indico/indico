// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

import {
  getGroup,
  computeYoffset,
  getGroups,
  layoutGroup,
  getWidthAndOffset,
  layoutGroupAfterMove,
} from './layout';
import {
  BlockEntry,
  BreakEntry,
  ChildBreakEntry,
  ChildContribEntry,
  ChildEntry,
  ContribEntry,
} from './types';

function makeCounter() {
  let id = 0;
  return {
    nextId: () => id++,
    resetCounter: () => (id = 0),
  };
}

const {nextId, resetCounter} = makeCounter();

function t(time: string) {
  const dt = `2021-01-01T${time}`;
  return moment(dt);
}

function scheduleMixin({
  time,
  column,
  maxColumn,
}: {
  time: string;
  column: number;
  maxColumn: number;
}) {
  return {
    startDt: t(time),
    x: 0,
    y: 0,
    width: 0,
    column,
    maxColumn,
  };
}

function contrib({
  id,
  title,
  time,
  duration,
  column = 0,
  maxColumn = 0,
}: {
  id?: number;
  title?: string;
  time: string;
  duration: number;
  column?: number;
  maxColumn?: number;
}): ContribEntry {
  if (id === undefined) {
    id = nextId();
  }
  if (title === undefined) {
    title = `Contrib ${id}`;
  }
  return {
    id,
    title,
    type: 'contrib',
    duration,
    ...scheduleMixin({time, column, maxColumn}),
  };
}

function childContrib({
  id,
  parentId,
  title,
  time,
  duration,
  column = 0,
  maxColumn = 0,
}: {
  id?: number;
  parentId: number;
  title?: string;
  time: string;
  duration: number;
  column?: number;
  maxColumn?: number;
}): ChildContribEntry {
  return {...contrib({id, title, time, duration, column, maxColumn}), parentId};
}

function break_({
  id,
  title,
  time,
  duration,
  column = 0,
  maxColumn = 0,
}: {
  id?: number;
  title?: string;
  time: string;
  duration: number;
  column?: number;
  maxColumn?: number;
}): BreakEntry {
  if (id === undefined) {
    id = nextId();
  }
  if (title === undefined) {
    title = `Break ${id}`;
  }
  return {
    id,
    title,
    type: 'break',
    duration,
    textColor: 'black',
    backgroundColor: 'white',
    ...scheduleMixin({time, column, maxColumn}),
  };
}

function childBreak({
  id,
  parentId,
  title,
  time,
  duration,
}: {
  id?: number;
  parentId: number;
  title?: string;
  time: string;
  duration: number;
}): ChildBreakEntry {
  return {...break_({id, title, time, duration}), parentId};
}

function block({
  id,
  title,
  children,
  time,
  duration,
  column = 0,
  maxColumn = 0,
}: {
  id?: number;
  title?: string;
  children: ChildEntry[];
  time: string;
  duration: number;
  column?: number;
  maxColumn?: number;
}): BlockEntry {
  if (id === undefined) {
    id = nextId();
  }
  if (title === undefined) {
    title = `Block ${id}`;
  }
  return {
    id,
    title,
    type: 'block',
    sessionId: 0,
    duration,
    children,
    ...scheduleMixin({time, column, maxColumn}),
  };
}

function parallelContribs({
  count,
  time,
  duration,
}: {
  count: number;
  time: string;
  duration: number;
}) {
  return Array.from({length: count}, (_, i) =>
    contrib({time, duration, column: i, maxColumn: count - 1})
  );
}

beforeEach(() => {
  resetCounter();
});

describe('getGroups()', () => {
  const cases = [
    {entries: [contrib({id: 0, time: '10:00', duration: 60})], groups: [new Set([0])]},
    {
      entries: [
        contrib({id: 0, time: '10:00', duration: 60}),
        contrib({id: 1, time: '11:00', duration: 60}),
      ],
      groups: [new Set([0]), new Set([1])],
    },
    {
      entries: [
        contrib({id: 0, time: '10:00', duration: 60}),
        contrib({id: 1, time: '10:30', duration: 60}),
      ],
      groups: [new Set([0, 1])],
    },
    {
      entries: [
        contrib({id: 0, time: '10:00', duration: 60}),
        contrib({id: 1, time: '11:00', duration: 60}),
        contrib({id: 2, time: '10:00', duration: 120}),
      ],
      groups: [new Set([0, 1, 2])],
    },
    {
      entries: [
        contrib({id: 0, time: '10:00', duration: 60}),
        contrib({id: 1, time: '11:00', duration: 60}),
        contrib({id: 2, time: '12:00', duration: 60}),
        contrib({id: 3, time: '10:30', duration: 90}),
        contrib({id: 4, time: '11:00', duration: 120}),
      ],
      groups: [new Set([0, 1, 2, 3, 4])],
    },
    {
      entries: [
        contrib({id: 0, time: '10:00', duration: 60}),
        contrib({id: 1, time: '11:00', duration: 60}),
        contrib({id: 2, time: '10:30', duration: 90}),
        contrib({id: 3, time: '12:00', duration: 60}),
      ],
      groups: [new Set([0, 1, 2]), new Set([3])],
    },
    {
      entries: [
        contrib({id: 0, time: '10:00', duration: 60}),
        contrib({id: 1, time: '10:20', duration: 60}),
        contrib({id: 2, time: '12:00', duration: 60}),
        contrib({id: 3, time: '12:20', duration: 60}),
        contrib({id: 4, time: '14:00', duration: 60}),
        contrib({id: 5, time: '14:20', duration: 60}),
      ],
      groups: [new Set([0, 1]), new Set([2, 3]), new Set([4, 5])],
    },
  ];

  for (const [i, c] of cases.entries()) {
    it(`(${i}) Should compute groups`, () => {
      expect(getGroups(c.entries)).toEqual(c.groups);
    });
  }
});

describe('getGroup()', () => {
  const cases = [
    {entries: [contrib({id: 0, time: '10:00', duration: 60})], group: new Set()},
    {
      entries: [
        contrib({id: 0, time: '10:00', duration: 60}),
        contrib({id: 1, time: '11:00', duration: 60}),
      ],
      group: new Set(),
    },
    {
      entries: [
        contrib({id: 0, time: '10:00', duration: 60}),
        contrib({id: 1, time: '10:30', duration: 60}),
      ],
      group: new Set([1]),
    },
    {
      entries: [
        contrib({id: 0, time: '10:00', duration: 60}),
        contrib({id: 1, time: '11:00', duration: 60}),
        contrib({id: 2, time: '10:00', duration: 120}),
      ],
      group: new Set([1, 2]),
    },
    {
      entries: [
        contrib({id: 0, time: '10:00', duration: 60}),
        contrib({id: 1, time: '11:00', duration: 60}),
        contrib({id: 2, time: '12:00', duration: 60}),
        contrib({id: 3, time: '10:30', duration: 90}),
        contrib({id: 4, time: '11:00', duration: 120}),
      ],
      group: new Set([1, 2, 3, 4]),
    },
    {
      entries: [
        contrib({id: 0, time: '10:00', duration: 60}),
        contrib({id: 1, time: '11:00', duration: 60}),
        contrib({id: 2, time: '10:30', duration: 90}),
        contrib({id: 3, time: '12:00', duration: 60}),
      ],
      group: new Set([1, 2]),
    },
  ];

  for (const [i, c] of cases.entries()) {
    it(`(${i}) Should compute the group`, () => {
      expect(getGroup(c.entries[0], c.entries.slice(1))).toEqual(c.group);
    });
  }
});

describe('layoutGroup()', () => {
  it('Should layout non-overlapping entries', () => {
    const entries = [
      contrib({time: '10:00', duration: 60}),
      contrib({time: '12:00', duration: 60}),
      contrib({time: '14:00', duration: 60}),
    ];
    const expected = [
      {...entries[0], y: 0, column: 0, maxColumn: 0},
      {...entries[1], y: 0, column: 0, maxColumn: 0},
      {...entries[2], y: 0, column: 0, maxColumn: 0},
    ];

    const newEntries = layoutGroup(entries);
    expect(newEntries).toEqual(expected);
  });

  it('Should layout parallel entries', () => {
    const entries = [
      contrib({time: '10:00', duration: 60}),
      contrib({time: '10:00', duration: 60}),
      contrib({time: '10:00', duration: 60}),
      contrib({time: '10:00', duration: 60}),
    ];
    const expected = [
      {...entries[0], y: 0, column: 0, maxColumn: 3},
      {...entries[1], y: 0, column: 1, maxColumn: 3},
      {...entries[2], y: 0, column: 2, maxColumn: 3},
      {...entries[3], y: 0, column: 3, maxColumn: 3},
    ];

    const newEntries = layoutGroup(entries);
    expect(newEntries).toEqual(expected);
  });

  it('(1) Should layout a mix of consecutive and parallel entries', () => {
    const entries = [
      contrib({time: '10:00', duration: 60}),
      contrib({time: '11:00', duration: 60}),
      contrib({time: '10:00', duration: 120}),
    ];
    const expected = [
      {...entries[0], y: 0, column: 0, maxColumn: 1},
      {...entries[1], y: 0, column: 0, maxColumn: 1},
      {...entries[2], y: 0, column: 1, maxColumn: 1},
    ];

    const newEntries = layoutGroup(entries);
    expect(newEntries).toEqual(expected);
  });

  it('(2) Should layout a mix of consecutive and parallel entries', () => {
    const entries = [
      contrib({time: '10:00', duration: 60}),
      contrib({time: '10:00', duration: 120}),
      contrib({time: '11:00', duration: 60}),
      contrib({time: '11:00', duration: 60}),
    ];
    const expected = [
      {...entries[0], y: 0, column: 0, maxColumn: 3},
      {...entries[1], y: 0, column: 1, maxColumn: 3},
      {...entries[2], y: 0, column: 2, maxColumn: 3},
      {...entries[3], y: 0, column: 3, maxColumn: 3},
    ];

    const newEntries = layoutGroup(entries);
    expect(newEntries).toEqual(expected);
  });
});

describe('layoutGroupAfterMove()', () => {
  it('No overlapping entries', () => {
    const group = [];
    const entry = contrib({time: '10:00', duration: 60});
    const mousePosition = 0.25;

    const expected = [{...entry, y: 0, column: 0, maxColumn: 0}];
    const newEntries = layoutGroupAfterMove(group, entry, mousePosition);
    expect(newEntries).toEqual(expected);
  });

  it('1 existing entry, mouse on the left side', () => {
    const group = [contrib({time: '10:00', duration: 60})];
    const entry = contrib({time: '10:00', duration: 60});
    const mousePosition = 0.25; // Mouse is in the left half of the timetable

    // The new entry should be placed in the first column (on the left)
    const expected = [
      {...entry, y: 0, column: 0, maxColumn: 1},
      {...group[0], y: 0, column: 1, maxColumn: 1},
    ];
    const newEntries = layoutGroupAfterMove(group, entry, mousePosition);
    expect(newEntries).toEqual(expected);
  });

  it('1 existing entry, mouse on the right side', () => {
    const group = [contrib({time: '10:00', duration: 60})];
    const entry = contrib({time: '10:00', duration: 60});
    const mousePosition = 0.75; // Mouse is in the right half of the timetable

    // The new entry should be placed in the second column (on the right)
    const expected = [
      {...group[0], y: 0, column: 0, maxColumn: 1},
      {...entry, y: 0, column: 1, maxColumn: 1},
    ];
    const newEntries = layoutGroupAfterMove(group, entry, mousePosition);
    expect(newEntries).toEqual(expected);
  });

  it('2 existing entries, selected column == 0', () => {
    const group = parallelContribs({count: 2, time: '10:00', duration: 60});
    const entry = contrib({time: '10:00', duration: 40});
    const mousePosition = 0.1; // The selected column is 0

    // The new entry should be placed in the first column
    const expected = [
      {...entry, y: 0, column: 0, maxColumn: 2},
      {...group[0], y: 0, column: 1, maxColumn: 2},
      {...group[1], y: 0, column: 2, maxColumn: 2},
    ];
    const newEntries = layoutGroupAfterMove(group, entry, mousePosition);
    expect(newEntries).toEqual(expected);
  });

  it('2 existing entries, selected column == 1', () => {
    const group = parallelContribs({count: 2, time: '10:00', duration: 60});
    const entry = contrib({time: '10:00', duration: 40});
    const mousePosition = 0.9; // The selected column is 1

    // The new entry should be placed in the last column
    const expected = [
      {...group[0], y: 0, column: 0, maxColumn: 2},
      {...group[1], y: 0, column: 1, maxColumn: 2},
      {...entry, y: 0, column: 2, maxColumn: 2},
    ];
    const newEntries = layoutGroupAfterMove(group, entry, mousePosition);
    expect(newEntries).toEqual(expected);
  });

  it('3 existing entries, selected column == 0', () => {
    const group = parallelContribs({count: 3, time: '10:00', duration: 60});
    const entry = contrib({time: '10:00', duration: 40});
    const mousePosition = 0.1;

    const expected = [
      {...entry, y: 0, column: 0, maxColumn: 3},
      {...group[0], y: 0, column: 1, maxColumn: 3},
      {...group[1], y: 0, column: 2, maxColumn: 3},
      {...group[2], y: 0, column: 3, maxColumn: 3},
    ];
    const newEntries = layoutGroupAfterMove(group, entry, mousePosition);
    expect(newEntries).toEqual(expected);
  });

  it('3 existing entries, selected column == 1', () => {
    const group = parallelContribs({count: 3, time: '10:00', duration: 60});
    const entry = contrib({time: '10:00', duration: 40});
    const mousePosition = 0.5;

    const expected = [
      {...group[0], y: 0, column: 0, maxColumn: 3},
      {...entry, y: 0, column: 1, maxColumn: 3},
      {...group[1], y: 0, column: 2, maxColumn: 3},
      {...group[2], y: 0, column: 3, maxColumn: 3},
    ];
    const newEntries = layoutGroupAfterMove(group, entry, mousePosition);
    expect(newEntries).toEqual(expected);
  });

  it('3 existing entries, selected column == 2', () => {
    const group = parallelContribs({count: 3, time: '10:00', duration: 60});
    const entry = contrib({time: '10:00', duration: 40});
    const mousePosition = 0.8;

    const expected = [
      {...group[0], y: 0, column: 0, maxColumn: 3},
      {...group[1], y: 0, column: 1, maxColumn: 3},
      {...group[2], y: 0, column: 2, maxColumn: 3},
      {...entry, y: 0, column: 3, maxColumn: 3},
    ];
    const newEntries = layoutGroupAfterMove(group, entry, mousePosition);
    expect(newEntries).toEqual(expected);
  });

  it('Right to left', () => {
    const group = [
      contrib({time: '10:00', duration: 40, column: 0, maxColumn: 2}),
      contrib({time: '10:00', duration: 40, column: 1, maxColumn: 2}),
    ];
    const entry = contrib({time: '10:00', duration: 40, column: 2, maxColumn: 2});
    const mousePosition = 0.5;

    const expected = [
      {...group[0], y: 0, column: 0, maxColumn: 2},
      {...entry, y: 0, column: 1, maxColumn: 2},
      {...group[1], y: 0, column: 2, maxColumn: 2},
    ];
    const newEntries = layoutGroupAfterMove(group, entry, mousePosition);
    expect(newEntries).toEqual(expected);
  });
});

describe('computeYOffset()', () => {
  const startHour = 10;

  it('Should compute the Y offset', () => {
    const entries = [
      contrib({time: '10:00', duration: 60}),
      contrib({time: '11:00', duration: 60}),
    ];
    const newEntries = computeYoffset(entries, startHour);

    expect(newEntries[0].y).toEqual(0);
    expect(newEntries[1].y).toEqual(120);
  });

  it('Should compute the Y offset of child entries', () => {
    const entries = [
      block({
        id: 0,
        time: '10:00',
        duration: 60,
        children: [childContrib({parentId: 0, time: '10:00', duration: 30})],
      }),
      block({
        id: 1,
        time: '11:00',
        duration: 60,
        children: [
          childContrib({parentId: 1, time: '11:00', duration: 30}),
          childContrib({parentId: 1, time: '11:30', duration: 30}),
        ],
      }),
    ];
    const copy = JSON.parse(JSON.stringify(entries));
    const newEntries = computeYoffset(entries, startHour);

    copy[0].y = 0;
    copy[0].children[0].y = 0;
    copy[1].y = 120;
    copy[1].children[0].y = 0;
    copy[1].children[1].y = 60;

    expect(copy).toEqual(JSON.parse(JSON.stringify(newEntries)));
  });
});

describe('getWidthAndOffset()', () => {
  it('Should compute width and offset from column/maxColumn', () => {
    expect(getWidthAndOffset(0, 0)).toEqual({width: '100%', offset: '0%'});
    expect(getWidthAndOffset(1, 1)).toEqual({width: '50%', offset: '50%'});
    expect(getWidthAndOffset(0, 1)).toEqual({width: '50%', offset: '0%'});
    expect(getWidthAndOffset(3, 3)).toEqual({width: '25%', offset: '75%'});
  });
});
