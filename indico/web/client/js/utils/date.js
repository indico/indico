// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import 'moment-timezone';

export function toMoment(dt, format, strict = false) {
  if (!dt) {
    return null;
  }
  const obj = moment(dt, format);
  if (strict && !obj.isValid()) {
    throw new Error(`Invalid dt: ${dt}`);
  }
  return obj;
}

export function serializeDate(dt, format = moment.HTML5_FMT.DATE) {
  return dt ? moment(dt).format(format) : null;
}

export function serializeTime(dt, format = moment.HTML5_FMT.TIME) {
  return dt ? moment(dt).format(format) : null;
}

export async function setMomentLocale(locale) {
  if (locale !== 'en' && locale !== 'en-us') {
    await import(/* webpackChunkName: "moment-locale/[request]" */ `moment/locale/${locale}`);
  }
  moment.locale([locale, 'en']);
}

export function dayRange(start, end, step = 1) {
  const next = start.clone();
  const result = [];
  while (next.isSameOrBefore(end)) {
    result.push(next.clone());
    next.add(step, 'd');
  }
  return result;
}

export function createDT(date, time) {
  const momentDate = moment(date, 'YYYY-MM-DD');
  const momentTime = moment(time, 'HH:mm');
  if (!momentDate.isValid() || !momentTime.isValid()) {
    return null;
  }

  return moment([...momentDate.toArray().splice(0, 3), ...momentTime.toArray().splice(3)]);
}

export function getBookingRangeMinDate(isAdminOverrideEnabled, gracePeriod) {
  if (isAdminOverrideEnabled) {
    return '';
  } else if (gracePeriod === null) {
    return serializeDate(moment());
  }
  return serializeDate(moment().subtract(gracePeriod, 'hour'));
}

export function isBookingStartDateValid(date, isAdminOverrideEnabled, gracePeriod) {
  if (!date || !date.isValid()) {
    return false;
  } else if (isAdminOverrideEnabled) {
    return true;
  } else if (gracePeriod === null) {
    return date.isSameOrAfter(moment(), 'day');
  }
  return date.isSameOrAfter(moment().subtract(gracePeriod, 'hour'), 'day');
}

export function isBookingStartDTValid(dt, isAdminOverrideEnabled, gracePeriod) {
  if (!dt || !dt.isValid()) {
    return false;
  } else if (isAdminOverrideEnabled) {
    return true;
  } else if (gracePeriod === null) {
    return dt.isSameOrAfter(moment().startOf('day'));
  }

  return dt.isSameOrAfter(moment().subtract(gracePeriod || 0, 'hour'), 'minute');
}

export function getMinimumBookingStartTime(startDate, isAdminOverrideEnabled, gracePeriod) {
  const today = moment();
  if (
    !moment(startDate).isValid() ||
    isAdminOverrideEnabled ||
    startDate.isAfter(today, 'day') ||
    gracePeriod === null
  ) {
    return null;
  }

  let minTime = null;
  if (startDate.isSame(today, 'day')) {
    const withGracePeriod = moment(today).subtract(gracePeriod, 'hour');
    if (withGracePeriod.date() === today.date()) {
      minTime = serializeTime(withGracePeriod);
    }
  } else {
    const withGracePeriod = moment(today).subtract(gracePeriod, 'hour');
    if (withGracePeriod.date() === startDate.date()) {
      minTime = serializeTime(withGracePeriod);
    }
  }
  return minTime;
}

export function initialEndTime(end) {
  const endOfDay = moment().endOf('day');
  return end > endOfDay ? endOfDay : end;
}

/**
 * Convert string date into date-agnostic datetime
 * @param {String} dt - String datetime to transform
 * @returns {moment.Moment} - Date-agnostic datetime
 */
export function getTime(dt) {
  return moment(dt).set({year: 0, month: 0, day: 0});
}

/**
 * Check whether there is a full overlap between two pre-bookings
 * @param {Array} preBookings - Array of two overlapping pre-bookings
 * @returns {Boolean} - Whether any of the two pre-bookings is fully overlapped by the other
 */
export function fullyOverlaps(preBookings) {
  return _.some(
    [preBookings, [...preBookings].reverse()].map(([preBookingA, preBookingB]) =>
      _.every(
        [preBookingA.startDt, preBookingA.endDt].map(dt =>
          getTime(dt).isBetween(
            getTime(preBookingB.startDt),
            getTime(preBookingB.endDt),
            null,
            '[]'
          )
        )
      )
    )
  );
}

export function localeUses24HourTime(locale) {
  return (
    new Intl.DateTimeFormat(locale, {
      hour: 'numeric',
    })
      .formatToParts(new Date(2020, 0, 1, 13))
      .find(part => part.type === 'hour').value.length === 2
  );
}

export function serializeDateTimeRange(startDt, endDt) {
  const startDate = serializeDate(startDt, 'LL');
  const startTime = serializeTime(startDt, 'LT');
  const endDate = serializeDate(endDt, 'LL');
  const endTime = serializeTime(endDt, 'LT');

  return moment(startDt).isSame(moment(endDt), 'day')
    ? `${startDate} ${startTime} - ${endTime}`
    : `${startDate} ${startTime} - ${endDate} ${endTime}`;
}

/**
 * Get the 3-letter weekday from a date string
 * @param {String} date - A date string (or undefined for current date)
 * @returns {String} - The 3-letter weekday (mon, tue, ...)
 */
export function getWeekday(date = undefined) {
  return moment(date)
    .locale('en')
    .format('ddd')
    .toLocaleLowerCase();
}

export function getToday() {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return now;
}

export function toDateString(date) {
  // We do not use ISO date format because it will be interpreted as UTC
  return date?.toDateString() || '';
}

export function toOptionalDate(dateString) {
  const date = new Date(dateString);
  if (!date.getTime()) {
    return;
  }
  date.setHours(0, 0, 0, 0);
  return date;
}

export function isSameDate(x, y) {
  return x?.toDateString() === y?.toDateString();
}

/**
 * Date range
 *
 * The base implementation is strict. If the range is not
 * specified, it will not count any date as being part of
 * the range, and if only one of the extremes is specified,
 * it will behave as if the date range includes only that
 * date. See OpenDateRange for a more lax version.
 */
export class DateRange {
  constructor(start, end) {
    this.start = toOptionalDate(start);
    this.end = toOptionalDate(end);
  }

  get isInvalid() {
    return !this.start && !this.end;
  }

  startsWith(date) {
    return isSameDate(date, this.start);
  }

  endsWith(date) {
    return isSameDate(date, this.end);
  }

  includes(date) {
    if (this.isInvalid) {
      return false;
    }
    if (!this.start) {
      return isSameDate(date, this.end);
    }
    if (!this.end) {
      return isSameDate(date, this.start);
    }
    return date >= this.start && date <= this.end;
  }

  clamp(date) {
    if (this.isInvalid) {
      return;
    }
    if (!this.start) {
      return new Date(this.end);
    }
    if (!this.end) {
      return new Date(this.start);
    }
    return new Date(Math.min(this.end, Math.max(this.start, date)));
  }

  toString() {
    return `${this.start}_${this.end}`;
  }
}

/**
 * Open date range
 *
 * Less strict version of DateRange which allows any date
 * if the range is not completely specified. Constructing
 * an empty open date range counts any date as being in
 * the range.
 */
export class OpenDateRange extends DateRange {
  includes(date) {
    if (this.isInvalid) {
      return true;
    }

    return date >= (this.start || -Infinity) && date <= (this.end || Infinity);
  }

  clamp(date) {
    if (!this.start && !this.end) {
      return date;
    }
    const start = this.start ?? -Infinity;
    const end = this.end ?? Infinity;
    return new Date(Math.min(end, Math.max(start, date)));
  }
}

/**
 * Sparse date range
 *
 * Takes multiple DateRange objects and provides a DateRange interface
 * that tests against all provided range. This allows us to have sparse
 * ranges.
 */
export class SparseDateRange {
  constructor(...ranges) {
    console.assert(ranges.every(r => r instanceof DateRange));
    this.ranges = ranges;
  }

  get startDate() {
    if (this.ranges.length) {
      return new Date(Math.min(...this.ranges.map(r => r.startDate).filter(Boolean)));
    }
    return undefined;
  }

  get endDate() {
    if (this.ranges.length) {
      return new Date(Math.max(...this.ranges.map(r => r.endDate).filter(Boolean)));
    }
    return undefined;
  }

  get isInvalid() {
    // Multi-range can never be invalid
    return false;
  }

  starsWith(date) {
    return this.ranges.any(r => r.startsWith(date));
  }

  endsWith(date) {
    return this.range.any(r => r.endsWith(date));
  }

  includes(date) {
    return this.ranges.some(r => r.includes(date));
  }

  clamp(date) {
    // Unlike clamp in other ranges, we are dealing with a sparse range,
    // so the date needs to fit within the closest one. We therefore first
    // need to identify which range is the closest.
    let minDist = Infinity;
    let closestRange;

    if (isNaN(date)) {
      return date;
    }

    for (const range of this.ranges) {
      if (range.includes(date)) {
        // if it's already in the range, stop
        return date;
      }
      const dist = Math.min(Math.abs(range.start - date), Math.abs(range.end - date));
      if (dist < minDist) {
        minDist = dist;
        closestRange = range;
      }
    }
    return closestRange.clamp(date);
  }
}
