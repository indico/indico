// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';

export function toMoment(dt, format) {
  return dt ? moment(dt, format) : null;
}

export function serializeDate(dt, format = moment.HTML5_FMT.DATE) {
  return dt ? moment(dt).format(format) : null;
}

export function serializeTime(dt, format = moment.HTML5_FMT.TIME) {
  return dt ? moment(dt).format(format) : null;
}

export async function setMomentLocale(locale) {
  const [language, territory] = locale.toLowerCase().split('_');
  let momentLocale;

  if (language === territory) {
    momentLocale = language;
  } else {
    momentLocale = `${language}-${territory}`;
  }

  if (momentLocale !== 'en') {
    await import(/* webpackChunkName: "moment-locale/[request]" */ `moment/locale/${momentLocale}`);
  }
  moment.locale(momentLocale);
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
