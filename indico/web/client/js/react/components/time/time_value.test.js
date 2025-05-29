// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Time, timeList, timePlaceholder} from './time_value';

function expectStep(list, step) {
  for (let i = 0; i < list.length - 1; i++) {
    expect(list[i + 1].value - list[i].value).toBe(step);
  }
}

describe('Time', () => {
  let assertOrig;

  beforeAll(() => {
    // Reduce the terminal noise while testing
    assertOrig = console.assert;
    console.assert = () => {};
  });

  afterAll(() => {
    console.assert = assertOrig;
  });

  it('should construct with minutes since midnight', () => {
    const t = new Time(202);
    expect(t.value).toBe(202);
    expect(t.hour).toBe(3);
    expect(t.minute).toBe(22);
  });

  it.each([[NaN], ['no numbers here'], [{}]])('should construct from invalid value, like %s', x => {
    const t = new Time(x);
    expect(t.hour).toBe(NaN);
    expect(t.minute).toBe(NaN);
  });

  it('should construct with hour and minute', () => {
    const t = Time.fromHour(3, 22);
    expect(t.value).toBe(202);
    expect(t.hour).toBe(3);
    expect(t.minute).toBe(22);
  });

  it.each([
    [NaN, 2],
    [5, NaN],
    [NaN, NaN],
    ['bogus', 2],
    [5, 'bogus'],
    ['bogus', 'fake'],
    [{}, 2],
    [5, {}],
    [{}, {}],
  ])('should construct with invalid hour and/or minute, like %s %s', (h, m) => {
    const t = Time.fromHour(h, m);
    expect(t.value).toBe(NaN);
    expect(t.hour).toBe(NaN);
    expect(t.minute).toBe(NaN);
    expect(t).toEqual(Time.fromHour(NaN, NaN));
  });

  it('should serialize to string', () => {
    const t = Time.fromHour(16, 5);
    expect(String(t)).toBe('16:05');
    expect(`${t}`).toBe('16:05');
    // eslint-disable-next-line prefer-template
    expect('' + t).toBe('965'); // Coerced to a number first, as intended!
    expect(t.toString()).toBe('16:05');
  });

  it('should serialize to string with zero-padded hour', () => {
    const t = Time.fromHour(5, 12);
    expect(t.toString()).toBe('05:12');
  });

  it('should serialize to string with invalid value', () => {
    const t = new Time(NaN);
    expect(t.toString()).toBe('Invalid time');
  });

  it('should convert to a date object', () => {
    const t = Time.fromHour(14, 20);
    const d = t.toDate();
    expect(d).toBeInstanceOf(Date);
    expect(d.getHours()).toBe(14);
    expect(d.getMinutes()).toBe(20);
  });

  it('should set the time on a specified date object', () => {
    const t = Time.fromHour(20, 7);
    const d = new Date(2022, 11, 20, 12, 33, 15);
    t.setTimeFor(d);
    expect(d.getHours()).toBe(20);
    expect(d.getMinutes()).toBe(7);
    expect(d.getSeconds()).toBe(0);
  });

  it('should diff between two Time objects', () => {
    const t1 = Time.fromHour(12, 30);
    const t2 = Time.fromHour(14, 0);
    const d1 = t1.duration(t2);
    const d2 = t2.duration(t1);

    expect(d1.value).toBe(90);
    expect(d1 - d2).toBe(0);
  });

  it.each([
    // 24-hour format
    ['00:00', 0, 0],
    ['00:01', 0, 1],
    ['03:10', 3, 10],
    ['12:00', 12, 0],
    ['12:01', 12, 1],
    ['19:10', 19, 10],
    ['23:59', 23, 59],

    // 24-hour with different separators
    ['19 : 10', 19, 10],
    ['19: 10', 19, 10],
    ['19 :10', 19, 10],
    ['19h10', 19, 10],
    ['19h 10', 19, 10],
    ['19 h10', 19, 10],
    ['19 h 10', 19, 10],
    ['19H10', 19, 10],
    ['19H 10', 19, 10],
    ['19 H10', 19, 10],
    ['19 H 10', 19, 10],
    ['19.10', 19, 10],
    ['19. 10', 19, 10],
    ['19 .10', 19, 10],
    ['19 . 10', 19, 10],

    // Compact input
    ['7', 7, 0],
    ['07', 7, 0],
    ['07:00', 7, 0],
    ['7:00', 7, 0],
    ['700', 7, 0],
    ['0730', 7, 30],
    ['1234', 12, 34],
    ['56', 5, 6],

    // Noisy but valid
    [' 7:00 ', 7, 0], // trim spaces
    ['07 : 00', 7, 0], // ignore internal spaces
  ])('should parse valid 24-hour formats, like "%s"', (input, hour, minute) => {
    expect(Time.fromString(input, '24h')).toEqual(Time.fromHour(hour, minute));
  });

  it.each([
    // Basic 12-hour format with AM/PM
    ['12:00 AM', 0, 0],
    ['12:01 AM', 0, 1],
    ['12:00 PM', 12, 0],
    ['12:01 PM', 12, 1],
    ['01:00 PM', 13, 0],
    ['11:59 PM', 23, 59],

    // No meridiem
    ['07:00', 7, 0],
    ['9:30', 9, 30],
    ['12:01', 0, 1],

    // AM variants
    ['7:00 am', 7, 0],
    ['7:00 a.m.', 7, 0],
    ['7:00 a. m.', 7, 0],
    ['7:00 a', 7, 0],
    ['7:00 AM', 7, 0],
    ['7:00 A.M.', 7, 0],
    ['7:00 A. M.', 7, 0],
    ['7:00 A', 7, 0],

    // PM variants
    ['7:00 pm', 19, 0],
    ['7:00 p.m.', 19, 0],
    ['7:00 p. m.', 19, 0],
    ['7:00 p', 19, 0],
    ['7:00 PM', 19, 0],
    ['7:00 P.M.', 19, 0],
    ['7:00 P. M.', 19, 0],
    ['7:00 P', 19, 0],

    // Compact format
    ['7a', 7, 0],
    ['2p', 14, 0],
    ['740a', 7, 40],
    ['240p', 14, 40],
    ['12p', 12, 0],
    ['13 PM', 13, 3],
    ['56p', 17, 6],

    // Noisy but valid
    [' 7:00 a m', 7, 0], // trim spaces
    ['07 : 00AM', 7, 0], // ignore internal spaces
  ])('should parse valid 12-hour format, like %s', (input, hour, minute) => {
    expect(Time.fromString(input, '12h')).toEqual(Time.fromHour(hour, minute));
  });

  it.each([
    '2400',
    '24:00',
    '1260',
    '12:60',
    '-1:00',
    '25:00',
    '07-00',
    '07::00',
    '::',
    'NaN',
    'null',
    'undefined',
    '',
    'true',
    'false',
    '{}',
    '[]',
    'lunch time',
    'midnightish',
    '12:345',
    '9:9999',
    '7:00🕖',
    '11:12am',
    '08:00 PM',
    '9:30 a.m.',
  ])('should fail to parse invalid 24-hour format, like "%s"', input => {
    expect(Time.fromString(input, '24h').value).toBe(NaN);
  });

  it.each([
    '0:00',
    '19:00',
    '0:30 PM',
    '0h30 PM',
    'am',
    'AM',
    'AM 07:00',
    '7 AM PM',
    'PM:07 00',
    '::',
    'NaN',
    'null',
    'undefined',
    '',
    'true',
    'false',
    '{}',
    '[]',
    'lunch time',
    'midnightish',
  ])('should fail to parse invalid 12-hour format like "%s"', input => {
    expect(Time.fromString(input, '12h').value).toBe(NaN);
  });

  it('should format to locale string', () => {
    const t = Time.fromString('14:00');

    expect(t.toLocaleString('en-US')).toBe('2:00 PM');
    expect(t.toLocaleString('de')).toBe('14:00');
    expect(t.toLocaleString('en-US', {hour: 'numeric', minute: 'numeric'})).toBe('2:00 PM');
  });

  it.each([
    ['0:00', '0h'],
    ['0:01', '0:01'],
    ['0:30', '0.5h'],
    ['0:59', '0:59'],
    ['1:00', '1h'],
    ['13:45', '13:45'],
  ])('should format time like %s to duration string', (timeString, durationString) => {
    const t = Time.fromString(timeString);

    expect(t.toDurationString()).toBe(durationString);
  });
});

describe('timeList', () => {
  it('should return a list of times in a day by default', () => {
    const l = timeList();

    expect(l.length).toBe(96);

    expect(l[0]).toEqual({
      label: '12:00 AM',
      time: '00:00',
      value: 0,
      durationLabel: '',
      duration: '',
      current: false,
    });

    expect(l.at(-1)).toEqual({
      label: '11:45 PM',
      time: '23:45',
      value: 1425,
      durationLabel: '',
      duration: '',
      current: false,
    });
  });

  it('should use 15 minutes as default step', () => {
    const l = timeList();

    expectStep(l, 15);
  });

  it('should use custom step when specified', () => {
    const l = timeList({step: 30});

    expect(l.length).toEqual(48);
    expectStep(l, 30);
  });

  it('should use a different locale when specified', () => {
    const l = timeList({locale: 'de'});

    expect(l[0].label).toBe('00:00');
  });

  it('should mark the current time', () => {
    const l = timeList({markCurrent: '12:45'});

    const marked = l.find(t => t.current);
    expect(marked).not.toBeUndefined();
    expect(marked.time).toBe('12:45');
  });

  it('should nor mark anything if no exact match', () => {
    const l = timeList({markCurrent: '12:03'});

    const marked = l.find(t => t.current);
    expect(marked).toBeUndefined();
  });
});

describe('timePlaceholder', () => {
  it.each([
    ['en-US', '--:-- AM/PM'],
    ['en-CA', '--:-- a.m./p.m.'],
    ['de-DE', '--:--'],
    ['fi-FI', '--.--'],
  ])('should return a placeholder for locale like %s', (locale, expected) => {
    expect(timePlaceholder(locale)).toBe(expected);
  });
});
