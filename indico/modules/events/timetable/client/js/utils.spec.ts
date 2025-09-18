// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

import {getDiffInDays} from './utils';

function dt(dtStr: string) {
  return moment(dtStr, 'YYYY-MM-DD HH:mm');
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
