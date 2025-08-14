// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// Note that this regex allows times without the meridiem portion. The rest of the
// code relies on knowing that we're parsing the 12-hour format time. Don't use this
// pattern to test *if* the time is in 12-hour format.
const LAX_T12H_PATTERN = /^(?<hours>0[1-9]|1[0-2]|[1-9])(?: *:? *(?<minutes>[0-5]?\d))? *(?<meridiem>[ap](?: ?m|\. ?m\.)?)?$/i;

// This is a strict 12h pattern that requires the meridiem part. It can be tested
// to see whether the string is a 12h time of day string.
const STRICT_T12H_PATTERN = /^(?<hours>0[1-9]|1[0-2]|[1-9])(?: *:? *(?<minutes>[0-5]?\d))? *(?<meridiem>[ap](?: ?m|\. ?m\.)?)$/i;

// Matches zero-padded and non-zero-padded hours and minutes with or without ':'.
const T24H_PATTERN = /^([01]\d|2[0-3]|\d)(?: *[:.h]? *([0-5]?\d))?$/i;

const meridiemFixups = {
  true: hour => (hour % 12) + 12,
  false: hour => hour % 12,
  undefined: hour => hour,
};

function zeroPad(n) {
  return n.toString().padStart(2, '0');
}

function regexMatch12To24h(match) {
  const hourString = match.groups.hours;
  const minuteString = match.groups.minutes ?? '0';
  const isPM = !!match.groups.meridiem?.toLowerCase().includes('p');
  const hour = meridiemFixups[isPM](parseInt(hourString, 10));
  const minute = parseInt(minuteString, 10);
  return [hour, minute];
}

function parse12h(timeOfDayString) {
  let match;

  if ((match = LAX_T12H_PATTERN.exec(timeOfDayString))) {
    return regexMatch12To24h(match);
  }

  return [NaN, NaN];
}

function parse24h(timeOfDayString) {
  let hour = NaN;
  let minute = NaN;

  const match = T24H_PATTERN.exec(timeOfDayString);

  if (match) {
    // Concatenate captured digits
    const digits = match[1] + (match[2] || '');

    if (digits.length >= 1 && digits.length <= 4) {
      if (digits.length <= 2) {
        hour = parseInt(digits, 10);
        minute = 0;
      } else if (digits.length === 3) {
        hour = parseInt(digits[0], 10);
        minute = parseInt(digits.slice(1), 10);
      } else {
        // length === 4
        hour = parseInt(digits.slice(0, 2), 10);
        minute = parseInt(digits.slice(2), 10);
      }

      // Validate ranges
      if (hour > 23 || minute > 59) {
        hour = NaN;
        minute = NaN;
      }
    }
  }

  return [hour, minute];
}

function parseAny(timeOfDayString) {
  let match;

  if ((match = STRICT_T12H_PATTERN.exec(timeOfDayString))) {
    return regexMatch12To24h(match);
  }

  // Use our new parse24h function for 24-hour format
  return parse24h(timeOfDayString);
}

const parsers = {
  '24h': parse24h,
  '12h': parse12h,
  'any': parseAny,
};

/**
 * Time represents the time of day or a duration within
 * a 24-hour period.
 *
 * Internally, the value is represented by a single number, number
 * of minutes since midnight. This class is used mostly to bundle
 * together convenience methods, and add clarity (compared to using
 * a naked number).
 */
export class Time {
  static MAX_TIME = 1439; // last minute of the day, 23:59 in minutes since 0:00

  static TIME_FORMAT_LOCALE = {
    '12h': 'en-US',
    '24h': 'de',
    'any': 'de',
  };

  static fromHour(hour, minute) {
    console.assert(
      isNaN(hour) || (hour >= 0 && hour <= 23),
      `Hour must be between 0 and 23, got ${hour}`
    );
    console.assert(
      isNaN(minute) || (minute >= 0 && minute <= 59),
      `Minute must be between 0 and 59, got ${minute}`
    );
    const minutesSinceMidnight = Math.min(
      this.MAX_TIME,
      Math.max(0, Number(hour) * 60 + Number(minute))
    );
    return new this(minutesSinceMidnight);
  }

  /**
   * The input string can be in one of the following formats:
   *
   * - HH:MM (zero-padded hours)
   * - H:MM (non-zero-padded hours)
   * - HH:M (non-zero-padded minutes)
   * - H:M (non-zero-padded hours and minutes)
   * - HHMM (no colon)
   * - HMM (non-zero-padded hours and no colon)
   * - HH:MMa (zero-padded hours, 'a' is any string with an 'a' or 'p')
   * - H:MMa (non-zero-padded hours, 'a' is any string with an 'a' or 'p')
   * - HHa (no minutes, 'a' is any string with an 'a' or 'p')
   * - Ha (non-zero-padded hours without minutes, 'a' is any string with an 'a' or 'p')
   *
   * Note that this function will also parse 'HM' (single digit hour,
   * single digit minutes) if the combination is valid (e.g., '56').
   *
   * The separator can be ':', '.', or 'h'. There is no support for Korean,
   * Burmese, and several other locales that use either non-Arabic numerals
   * or non-Latin meridiem indicators, or locaes where meridiem indicators
   * are prefixed.
   *
   * How this is interpretted depends on the format parameter which can be
   * '24h' or '12h' (default is '24h').
   *
   * See tests for a more complete list of examples.
   */
  static fromString(timeOfDayString, format = 'any') {
    const parser = parsers[format] || parseAny;
    const [hour, minute] = parser(timeOfDayString.trim());
    return this.fromHour(hour, minute);
  }

  constructor(minutesSinceMidnight) {
    this.value = minutesSinceMidnight;
  }

  get hour() {
    return Math.floor(this.value / 60);
  }

  get minute() {
    return Math.floor(this.value % 60);
  }

  duration(other) {
    const diff = Math.abs(other.value - this.value);
    return new Time(diff);
  }

  addDuration(duration) {
    this.value = Math.min(this.constructor.MAX_TIME, this.value + duration.value);
    return this;
  }

  setTimeFor(date) {
    date.setHours(this.hour, this.minute, 0, 0);
  }

  get isValid() {
    return !Number.isNaN(this.value);
  }

  toDate() {
    const date = new Date();
    date.setHours(this.hour, this.minute, 0, 0);
    return date;
  }

  [Symbol.toPrimitive](hint) {
    if (hint === 'string') {
      return this.toString();
    }
    return this.value;
  }

  toString() {
    if (!this.isValid) {
      return 'Invalid time';
    }
    return `${zeroPad(this.hour)}:${zeroPad(this.minute)}`;
  }

  toSafeString() {
    if (!this.isValid) {
      return '';
    }
    return this.toString();
  }

  toShortString() {
    if (isNaN(this.value)) {
      return '';
    }
    return `${this.hour}:${zeroPad(this.minute)}`;
  }

  toFormattedString(timeFormat) {
    return this.toLocaleString(this.constructor.TIME_FORMAT_LOCALE[timeFormat]);
  }

  toLocaleString(locale, options = {hour: 'numeric', minute: 'numeric'}) {
    return this.toDate().toLocaleTimeString(locale, options);
  }

  toJSON() {
    return this.value;
  }
}

export function timeList(options = {}) {
  const {
    markCurrent = '',
    startTime = '',
    step = 15,
    minTime = '0:00',
    maxTime = '23:59',
    timeFormat = 'auto',
  } = options;

  const min = Time.fromString(minTime, '24h').value;
  const max = Time.fromString(maxTime, '24h').value;
  const current = markCurrent ? Time.fromString(markCurrent, '24h') : null;
  const start = startTime ? Time.fromString(startTime, '24h') : null;

  const list = [];
  for (let i = min; i <= max; i += step) {
    const t = new Time(i);
    const duration = start ? t.duration(start) : null;
    list.push({
      label: t.toFormattedString(timeFormat),
      time: t.toString(),
      value: t.value,
      duration,
      current: current?.value === t.value,
    });
  }
  return list;
}

export function timePlaceholder(locale) {
  return new Date(1, 1, 1, 9, 0)
    .toLocaleTimeString(locale, {
      hour: '2-digit',
      minute: '2-digit',
    })
    .toLowerCase()
    .replace('09', '--')
    .replace('00', '--')
    .replace('am', 'AM/PM')
    .replace('a.m.', 'a.m./p.m.');
}
