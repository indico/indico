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

  it('should add duration to time', () => {
    const t = Time.fromString('10:30');
    const duration = new Time(90); // 90 minutes

    t.addDuration(duration);

    expect(t.toString()).toBe('12:00');
    expect(t.hour).toBe(12);
    expect(t.minute).toBe(0);
  });

  it('should add multiple durations', () => {
    const t = Time.fromString('8:00');
    const duration1 = new Time(30);
    const duration2 = new Time(45);

    t.addDuration(duration1);
    t.addDuration(duration2);

    expect(t.toString()).toBe('09:15');
    expect(t.hour).toBe(9);
    expect(t.minute).toBe(15);
  });

  it('should clamp to maximum time when adding duration', () => {
    const t = Time.fromString('23:30');
    const duration = new Time(60); // 60 minutes

    t.addDuration(duration);

    expect(t.toString()).toBe('23:59');
    expect(t.value).toBe(Time.MAX_TIME);
  });

  it('should handle edge case at end of day', () => {
    const t = Time.fromString('23:59');
    const duration = new Time(1); // 1 minute

    t.addDuration(duration);

    expect(t.toString()).toBe('23:59');
    expect(t.value).toBe(Time.MAX_TIME);
  });

  it('should handle zero duration', () => {
    const t = Time.fromString('15:45');
    const duration = new Time(0);

    t.addDuration(duration);

    expect(t.toString()).toBe('15:45');
  });

  it('should work with duration from duration() method', () => {
    const t1 = Time.fromString('9:00');
    const t2 = Time.fromString('10:30');
    const duration = t1.duration(t2);
    const t3 = Time.fromString('14:00');

    t3.addDuration(duration);

    expect(t3.toString()).toBe('15:30');
  });

  it('should handle invalid duration (NaN)', () => {
    const t = Time.fromString('10:30');
    const invalidDuration = Time.fromString('invalid time');

    t.addDuration(invalidDuration);

    expect(t.value).toBe(NaN);
    expect(t.toString()).toBe('Invalid time');
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
    ['233', 2, 33],
    ['933', 9, 33],
    ['123', 1, 23],

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
    // 12-hour format with meridiem (should parse as 12-hour)
    ['12:00 AM', 0, 0],
    ['12:01 AM', 0, 1],
    ['12:00 PM', 12, 0],
    ['12:01 PM', 12, 1],
    ['01:00 PM', 13, 0],
    ['11:59 PM', 23, 59],
    ['7:00 am', 7, 0],
    ['7:00 p.m.', 19, 0],
    ['7:00 P', 19, 0],
    ['7a', 7, 0],
    ['2p', 14, 0],
    ['740a', 7, 40],
    ['240p', 14, 40],
    ['12p', 12, 0],
    ['13 PM', 13, 3],
    ['56p', 17, 6],
    [' 7:00 a m', 7, 0],
    ['07 : 00AM', 7, 0],

    // 24-hour format (no meridiem, should parse as 24-hour)
    ['00:00', 0, 0],
    ['00:01', 0, 1],
    ['03:10', 3, 10],
    ['12:00', 12, 0],
    ['12:01', 12, 1],
    ['19:10', 19, 10],
    ['23:59', 23, 59],
    ['19h10', 19, 10],
    ['19H 10', 19, 10],
    ['19.10', 19, 10],
    ['7', 7, 0],
    ['07', 7, 0],
    ['700', 7, 0],
    ['0730', 7, 30],
    ['1234', 12, 34],
    ['233', 2, 33],
    ['933', 9, 33],
    ['123', 1, 23],
    [' 7:00 ', 7, 0],
    ['07 : 00', 7, 0],
  ])(
    'should parse valid time formats with automatic format detection, like "%s"',
    (input, hour, minute) => {
      expect(Time.fromString(input, 'any')).toEqual(Time.fromHour(hour, minute));
    }
  );

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

  it.each([
    // Invalid formats that should fail for both 12h and 24h
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

    // Invalid 12-hour formats (has meridiem but invalid structure)
    '0:00 PM', // Hour 0 is invalid in 12-hour
    '0:30 PM', // Hour 0 is invalid in 12-hour
    '0h30 PM', // Hour 0 is invalid in 12-hour
    'am', // No time component
    'AM', // No time component
    'AM 07:00', // Meridiem before time
    '7 AM PM', // Double meridiem
    'PM:07 00', // Meridiem in wrong position
  ])('should fail to parse invalid formats with automatic format selection, like "%s"', input => {
    expect(Time.fromString(input, 'any').value).toBe(NaN);
  });

  it('should format to locale string', () => {
    const t = Time.fromString('14:00');

    expect(t.toLocaleString('en-US')).toBe('2:00 PM');
    expect(t.toLocaleString('de')).toBe('14:00');
    expect(t.toLocaleString('en-US', {hour: 'numeric', minute: 'numeric'})).toBe('2:00 PM');
  });

  it.each([
    ['0:00', '12h', '12:00 AM'],
    ['0:00', '24h', '00:00'],
    ['0:00', 'any', '00:00'],
    ['8:00', '12h', '8:00 AM'],
    ['8:00', '24h', '08:00'],
    ['8:00', 'any', '08:00'],
    ['12:00', '12h', '12:00 PM'],
    ['12:00', '24h', '12:00'],
    ['12:00', 'any', '12:00'],
  ])('should format a time like %s using format %s', (timeString, timeFormat, expected) => {
    expect(Time.fromString(timeString, '24h').toFormattedString(timeFormat)).toBe(expected);
  });

  it('should use automatic selection of time format by default', () => {
    const sample12hA = Time.fromString('12:01', '12h');
    const sampleAnyA = Time.fromString('12:01', 'any');
    const sampleDefA = Time.fromString('12:01');

    expect(sample12hA.value).not.toBe(sampleAnyA.value);
    expect(sampleAnyA.value).toBe(sampleDefA.value);

    const sample24hB = Time.fromString('7:00 PM', '24h');
    const sampleAnyB = Time.fromString('7:00 PM', 'any');
    const sampleDefB = Time.fromString('7:00 PM');

    expect(sample24hB.value).not.toBe(sampleAnyB.value);
    expect(sampleAnyB.value).toBe(sampleDefB.value);
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
      duration: null,
      current: false,
    });

    expect(l.at(-1)).toEqual({
      label: '11:45 PM',
      time: '23:45',
      value: 1425,
      duration: null,
      current: false,
    });
  });

  it('should start from minTime', () => {
    const l = timeList({minTime: '14:55'});

    expect(l[0].time).toBe('14:55');
    expect(l[1].time).toBe('15:10');
    expect(l.at(-1).time).toBe('23:55');
  });

  it('should end before maxTime', () => {
    const l = timeList({maxTime: '14:55'});

    expect(l[0].time).toBe('00:00');
    expect(l.at(-1).time).toBe('14:45');
  });

  it('should include the maxTime', () => {
    const l = timeList({maxTime: '13:30'});

    expect(l[0].time).toBe('00:00');
    expect(l.at(-1).time).toBe('13:30');
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

  it('should use a different time format when specified', () => {
    const l = timeList({timeFormat: '24h'});

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

  it('should return durations when startTime is specified', () => {
    const l = timeList({minTime: '13:00', startTime: '12:05'});

    expect(l[0].duration).toEqual(new Time(55));
    expect(l[1].duration).toEqual(new Time(70));
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
