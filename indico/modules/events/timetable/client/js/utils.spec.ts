// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

import {BlockEntry, ChildEntry, Entry, EntryType} from './types';
import {computeOverlappingEntryIds, flattenEntries, getDiffInDays} from './utils';

function dt(dtStr: string) {
  return moment(dtStr, 'YYYY-MM-DD HH:mm');
}

function createEntry(overrides: Partial<Entry> = {}): Entry {
  const {
    startDt = moment('2025-01-29 09:00', 'YYYY-MM-DD HH:mm'),
    type = EntryType.Contribution,
    id = `${type[0]}${Math.random().toString(36).slice(2, 7)}`,
    duration = 30,
  } = overrides;

  const base = {
    id,
    startDt,
    duration,
    type,
    ...overrides,
  };

  if (overrides.type === EntryType.SessionBlock && !(base as BlockEntry).children) {
    (base as BlockEntry).children = overrides?.children ?? [];
  }

  return base as Entry;
}

describe('getDiffInDays()', () => {
  it('Should compute one day difference between two dates within 24 hours of each other', () => {
    const dt1 = dt('2025-09-18 21:00');
    const dt2 = dt('2025-09-19 14:00');

    expect(getDiffInDays(dt1, dt2)).toEqual(1);
  });

  it('Should compute same day difference regardless of argument order', () => {
    const startDay = Math.floor(Math.random() * 10);
    const endDay = startDay + Math.floor(Math.random() * 15);
    const dt1 = dt(`2025-09-${startDay} 21:00`);
    const dt2 = dt(`2025-09-${endDay} 16:00`);

    expect(getDiffInDays(dt1, dt2)).toEqual(getDiffInDays(dt2, dt1));
  });

  it('Should compute correct difference across long period', () => {
    const dayDiff = Math.floor(Math.random() * 500) + 30;
    const dt1 = dt(`2024-11-01 01:01`);
    const dt2 = dt1.clone().add(dayDiff, 'days');

    expect(getDiffInDays(dt1, dt2)).toEqual(dayDiff);
  });

  it('Should compute difference of 0 days on same day', () => {
    const dt1 = dt(`2024-11-01 00:00`);
    const dt2 = dt(`2024-11-01 23:59`);

    expect(getDiffInDays(dt1, dt2)).toEqual(0);
  });
});

describe('computeOverlappingEntryIds', () => {
  it('returns empty set for empty or single list', () => {
    expect(computeOverlappingEntryIds([])).toEqual(new Set());
    const single = [createEntry({id: 'c1'})];
    expect(computeOverlappingEntryIds(single).size).toBe(0);
  });

  it('detects simple overlap between two entries', () => {
    const a = createEntry({
      id: 'c1',
      startDt: moment('2026-01-29 10:00', 'YYYY-MM-DD HH:mm'),
      duration: 60,
    });
    const b = createEntry({
      id: 'c2',
      startDt: moment('2026-01-29 10:30', 'YYYY-MM-DD HH:mm'),
      duration: 30,
    });
    const result = computeOverlappingEntryIds([a, b]);
    expect(result).toEqual(new Set(['c1', 'c2']));
  });

  it('does not treat touching intervals as overlapping', () => {
    const a = createEntry({
      id: 'c1',
      startDt: moment('2026-01-29 10:00', 'YYYY-MM-DD HH:mm'),
      duration: 60,
    });
    const b = createEntry({
      id: 'c2',
      startDt: moment('2026-01-29 11:00', 'YYYY-MM-DD HH:mm'),
      duration: 30,
    });
    const result = computeOverlappingEntryIds([a, b]);
    expect(result).toEqual(new Set());
  });

  it('handles nested children inside session blocks and reports overlapping child ids', () => {
    const child1 = createEntry({
      id: 'c1',
      startDt: moment('2026-01-29 10:00', 'YYYY-MM-DD HH:mm'),
      duration: 60,
    }) as ChildEntry;
    const child2 = createEntry({
      // Does not overlap
      id: 'c2',
      startDt: moment('2026-01-29 12:00', 'YYYY-MM-DD HH:mm'),
      duration: 30,
    }) as ChildEntry;
    const child3 = createEntry({
      id: 'c3',
      startDt: moment('2026-01-29 10:20', 'YYYY-MM-DD HH:mm'),
      duration: 30,
    }) as ChildEntry;
    const block = createEntry({
      id: 's1',
      type: EntryType.SessionBlock,
      startDt: moment('2026-01-29 10:00', 'YYYY-MM-DD HH:mm'),
      duration: 180,
      children: [child1, child2, child3],
    }) as BlockEntry;
    const contrib = createEntry({
      id: 'c4',
      type: EntryType.Contribution,
      startDt: moment('2026-01-29 10:30', 'YYYY-MM-DD HH:mm'),
      duration: 30,
    });

    const overlaps = computeOverlappingEntryIds([block, contrib]);
    expect(overlaps).toEqual(new Set(['c1', 'c3', 'b1', 'c4']));
  });
});

describe('flattenEntries', () => {
  it('puts all entries and children on same depth', () => {
    const child = createEntry({
      id: 'c1',
    }) as ChildEntry;
    const block = createEntry({
      id: 's1',
      type: EntryType.SessionBlock,
      duration: 60,
      children: [child],
    }) as BlockEntry;
    const contrib = createEntry({
      id: 'c2',
      duration: 20,
    });

    const flat = flattenEntries([block, contrib]);
    expect(flat.length).toBe(3);
  });

  it('handles empty children arrays', () => {
    const block = createEntry({
      id: 's1',
      type: EntryType.SessionBlock,
      duration: 60,
      children: [],
    }) as BlockEntry;
    const flat = flattenEntries([block]);
    expect(flat.length).toBe(1);
  });
});
