// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {getToday} from './date';

export function getWeekInfoForLocale(locale) {
  let weekInfo = new Intl.Locale(locale).weekInfo;
  weekInfo ??= {firstDay: 7, weekend: [6, 7]}; /* Firefox 😭 */
  weekInfo.weekDays = [];
  for (let i = weekInfo.firstDay, end = i + 7; i < end; i++) {
    weekInfo.weekDays.push(i % 7 || 7);
  }
  return weekInfo;
}

export function getFirstDayOfWeek(weekInfo, date) {
  const offset = weekInfo.weekDays.indexOf(date.getDay() || 7);
  const firstDayOfWeek = new Date(date);
  firstDayOfWeek.setDate(firstDayOfWeek.getDate() - offset);
  return firstDayOfWeek;
}

export function getWeekdayNames(weekInfo, locale) {
  const date = getFirstDayOfWeek(weekInfo, getToday());
  const weekdayNames = [];
  for (let i = 0; i < 7; i++) {
    weekdayNames.push({
      full: date.toLocaleDateString(locale, {weekday: 'long'}),
      short: date.toLocaleDateString(locale, {weekday: 'narrow'}),
    });
    date.setDate(date.getDate() + 1);
  }
  return weekdayNames;
}
