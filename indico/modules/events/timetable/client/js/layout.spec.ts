// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

import {getGroup, computeYoffset, getGroups, layoutGroup} from './layout';
import {
  BlockEntry,
  BreakEntry,
  ChildBreakEntry,
  ChildContribEntry,
  ChildEntry,
  ContribEntry,
} from './types';

function p(value: number) {
  return `${100 * value}%`;
}

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

function scheduleMixin(time: string) {
  return {
    startDt: t(time),
    x: 0,
    y: 0,
    width: 0,
    column: 0,
    maxColumn: 0,
  };
}

function contrib({
  id,
  title,
  time,
  duration,
}: {
  id?: number;
  title?: string;
  time: string;
  duration: number;
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
    ...scheduleMixin(time),
  };
}

function childContrib({
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
}): ChildContribEntry {
  return {...contrib({id, title, time, duration}), parentId};
}

function break_({
  id,
  title,
  time,
  duration,
}: {
  id?: number;
  title?: string;
  time: string;
  duration: number;
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
    ...scheduleMixin(time),
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
}: {
  id?: number;
  title?: string;
  children: ChildEntry[];
  time: string;
  duration: number;
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
    ...scheduleMixin(time),
  };
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
    it(`Should compute groups ${i}`, () => {
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
    it(`Should compute the group ${i}`, () => {
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
      {...entries[0], x: '0%', y: 0, width: '100%', column: 0, maxColumn: 0},
      {...entries[1], x: '0%', y: 0, width: '100%', column: 0, maxColumn: 0},
      {...entries[2], x: '0%', y: 0, width: '100%', column: 0, maxColumn: 0},
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
      {...entries[0], x: p(0 / 4), y: 0, width: p(1 / 4), column: 0, maxColumn: 3},
      {...entries[1], x: p(1 / 4), y: 0, width: p(1 / 4), column: 1, maxColumn: 3},
      {...entries[2], x: p(2 / 4), y: 0, width: p(1 / 4), column: 2, maxColumn: 3},
      {...entries[3], x: p(3 / 4), y: 0, width: p(1 / 4), column: 3, maxColumn: 3},
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
      {...entries[0], x: p(0 / 2), y: 0, width: p(1 / 2), column: 0, maxColumn: 1},
      {...entries[1], x: p(0 / 2), y: 0, width: p(1 / 2), column: 0, maxColumn: 1},
      {...entries[2], x: p(1 / 2), y: 0, width: p(1 / 2), column: 1, maxColumn: 1},
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
      {...entries[0], x: p(0 / 4), y: 0, width: p(1 / 4), column: 0, maxColumn: 3},
      {...entries[1], x: p(1 / 4), y: 0, width: p(1 / 4), column: 1, maxColumn: 3},
      {...entries[2], x: p(2 / 4), y: 0, width: p(1 / 4), column: 2, maxColumn: 3},
      {...entries[3], x: p(3 / 4), y: 0, width: p(1 / 4), column: 3, maxColumn: 3},
    ];

    const newEntries = layoutGroup(entries);
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
