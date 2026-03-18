// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

import {DateRange, OpenDateRange, getDisabledHours, getDisabledMinutes} from 'indico/utils/date';

describe('DateRange', () => {
  describe('clamp', () => {
    const doClamp = (start, end) => {
      const range = new DateRange(start, end);
      const targets = [new Date('2024 Aug 2'), new Date('2024 Aug 9'), new Date('2024 Aug 14')];
      return targets.map(t => range.clamp(t));
    };

    it('should clamp a date to its range', () => {
      const start = new Date('2024 Aug 8');
      const end = new Date('2024 Aug 12');

      const results = doClamp(start, end);

      results.forEach(r => {
        expect(r.getTime()).toBeGreaterThanOrEqual(start.getTime());
        expect(r.getTime()).toBeLessThanOrEqual(end.getTime());
      });
    });

    it('should return start if only start is specified', () => {
      const start = new Date('2024 Aug 8');
      const end = undefined;

      const results = doClamp(start, end);

      results.forEach(r => expect(expect(r).toEqual(start)));
    });

    it('should return end if only end is specified', () => {
      const start = undefined;
      const end = new Date('2024 Aug 12');

      const results = doClamp(start, end);

      results.forEach(r => expect(expect(r).toEqual(end)));
    });

    it('should return undefined if no range is specified', () => {
      const start = undefined;
      const end = undefined;

      const results = doClamp(start, end);

      results.forEach(r => expect(expect(r).toBeUndefined()));
    });
  });
});

describe('OpenDateRange', () => {
  describe('clamp', () => {
    const targets = [new Date('2024 Aug 2'), new Date('2024 Aug 9'), new Date('2024 Aug 14')];
    const doClamp = (start, end) => {
      const range = new OpenDateRange(start, end);
      return targets.map(t => range.clamp(t));
    };

    test('should clamp a date to its range', () => {
      const start = new Date('2024 Aug 8');
      const end = new Date('2024 Aug 12');

      const results = doClamp(start, end);

      results.forEach(r => {
        expect(r.getTime()).toBeGreaterThanOrEqual(start.getTime());
        expect(r.getTime()).toBeLessThanOrEqual(end.getTime());
      });
    });

    test('should clamp a date to start if only start is specified', () => {
      const start = new Date('2024 Aug 8');
      const end = undefined;

      const results = doClamp(start, end);

      results.forEach(r => {
        expect(r.getTime()).toBeGreaterThanOrEqual(start.getTime());
      });
    });

    test('should clamp a date to end if only end is specified', () => {
      const start = undefined;
      const end = new Date('2024 Aug 12');

      const results = doClamp(start, end);

      results.forEach(r => {
        expect(r.getTime()).toBeLessThanOrEqual(end.getTime());
      });
    });

    test('if range is not specified, dates are not clamped', () => {
      const start = undefined;
      const end = undefined;

      const results = doClamp(start, end);

      results.forEach((r, i) => {
        expect(r).toEqual(targets[i]);
      });
    });
  });
});

describe('getDisabledHours', () => {
  const dt = moment('2025-01-15 12:00');

  it('disables no hours when no constraints are provided', () => {
    expect(getDisabledHours(dt)).toEqual([]);
  });

  it('disables no hours when date is different from constraints', () => {
    const minStartDt = moment('2025-01-14 09:30');
    expect(getDisabledHours(dt, minStartDt)).toEqual([]);
  });

  it('disables hours before minStartDt when on same day', () => {
    const minStartDt = moment('2025-01-15 09:30');
    const result = getDisabledHours(dt, minStartDt);
    expect(result).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8]);
  });

  it('disables hours after maxEndDt when on same day', () => {
    const maxEndDt = moment('2025-01-15 17:00');
    const result = getDisabledHours(dt, undefined, maxEndDt);
    expect(result).toEqual([18, 19, 20, 21, 22, 23]);
  });

  it('disables hours outside range when both constraints are on same day', () => {
    const minStartDt = moment('2025-01-15 09:30');
    const maxEndDt = moment('2025-01-15 17:00');
    const result = getDisabledHours(dt, minStartDt, maxEndDt);
    expect(result).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 18, 19, 20, 21, 22, 23]);
  });

  it('handles edge case: minStartDt at midnight (hour 0)', () => {
    const minStartDt = moment('2025-01-15 00:00');
    const result = getDisabledHours(dt, minStartDt);
    expect(result).toEqual([]);
  });

  it('handles edge case: maxEndDt at midnight (hour 0)', () => {
    const maxEndDt = moment('2025-01-15 00:00');
    const result = getDisabledHours(dt, undefined, maxEndDt);
    expect(result).toEqual([
      1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
    ]);
  });

  it('handles edge case: minStartDt at last hour (hour 23)', () => {
    const minStartDt = moment('2025-01-15 23:30');
    const result = getDisabledHours(dt, minStartDt);
    expect(result).toEqual([
      0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
    ]);
  });

  it('handles edge case: maxEndDt at last hour (hour 23)', () => {
    const maxEndDt = moment('2025-01-15 23:59');
    const result = getDisabledHours(dt, undefined, maxEndDt);
    expect(result).toEqual([]);
  });

  it('handles same minStartDt and maxEndDt hour', () => {
    const minStartDt = moment('2025-01-15 14:15');
    const maxEndDt = moment('2025-01-15 14:45');
    const result = getDisabledHours(dt, minStartDt, maxEndDt);
    expect(result).toEqual([
      0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23,
    ]);
  });
});

describe('getDisabledMinutes', () => {
  const dt = moment('2025-01-15 12:00');

  it('disables no minutes when no constraints are provided', () => {
    expect(getDisabledMinutes(12, dt)).toEqual([]);
  });

  it('disables no minutes when date is different from constraints', () => {
    const minStartDt = moment('2025-01-14 09:30');
    expect(getDisabledMinutes(12, dt, minStartDt)).toEqual([]);
  });

  it('disables minutes before minStartDt when hour matches', () => {
    const minStartDt = moment('2025-01-15 09:30');
    const result = getDisabledMinutes(9, dt, minStartDt);
    expect(result).toEqual([...Array(30).keys()]);
  });

  it('disables minutes after maxEndDt when hour matches', () => {
    const maxEndDt = moment('2025-01-15 17:15');
    const result = getDisabledMinutes(17, dt, undefined, maxEndDt);
    expect(result).toEqual([...Array(60).keys()].filter(m => m > 15));
  });

  it('disables all minutes when hour is before minStartDt hour', () => {
    const minStartDt = moment('2025-01-15 09:30');
    const result = getDisabledMinutes(8, dt, minStartDt);
    expect(result).toEqual([...Array(60).keys()]);
  });

  it('disables all minutes when hour is after maxEndDt hour', () => {
    const maxEndDt = moment('2025-01-15 17:15');
    const result = getDisabledMinutes(18, dt, undefined, maxEndDt);
    expect(result).toEqual([...Array(60).keys()]);
  });

  it('disables no minutes when hour is after minStartDt hour', () => {
    const minStartDt = moment('2025-01-15 09:30');
    const result = getDisabledMinutes(10, dt, minStartDt);
    expect(result).toEqual([]);
  });

  it('disables no minutes when hour is before maxEndDt hour', () => {
    const maxEndDt = moment('2025-01-15 17:15');
    const result = getDisabledMinutes(16, dt, undefined, maxEndDt);
    expect(result).toEqual([]);
  });

  it('handles edge case: minute 0 as maxEndDt', () => {
    const maxEndDt = moment('2025-01-15 17:00');
    const result = getDisabledMinutes(17, dt, undefined, maxEndDt);
    expect(result).toEqual([...Array(60).keys()].filter(m => m > 0));
  });

  it('handles edge case: minute 59 as minStartDt', () => {
    const minStartDt = moment('2025-01-15 09:59');
    const result = getDisabledMinutes(9, dt, minStartDt);
    expect(result).toEqual([...Array(59).keys()]);
  });

  it('handles both constraints on same day and same hour', () => {
    const minStartDt = moment('2025-01-15 14:15');
    const maxEndDt = moment('2025-01-15 14:45');
    const result = getDisabledMinutes(14, dt, minStartDt, maxEndDt);
    expect(result).toEqual([
      0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
      57, 58, 59,
    ]);
  });
});
