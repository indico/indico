// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {DateRange, OpenDateRange} from 'indico/utils/date';

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
