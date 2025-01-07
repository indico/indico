// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import preval from 'preval.macro';

import {getToday} from './date';

// This is used in browsers that do not support Intl API.
// Only those items where the data differs from the generic
// fallback are listed.
// language=JavaScript
const WEEK_INFO = preval`
const fs = require('node:fs');
const path = require('node:path');
const MONDAY = 1;
const SATURDAY = 6;

// Traverse up to package.json and then calculate
// translations path from there
let packageJsonDir = __dirname;
while (packageJsonDir !== path.dirname(packageJsonDir)) {
  if (fs.existsSync(path.join(packageJsonDir, 'package.json'))) {
    break;
  }
  packageJsonDir = path.dirname(packageJsonDir);
}
const translationDir = path.resolve(packageJsonDir, 'indico/translations');

const localeData = {};
const paths = fs.readdirSync(translationDir, {withFileTypes: true});

for (const p of paths) {
  if (p.isDirectory()) {
    // Transform locale to a browser-compatible version
    const parts = p.name.split('_');
    const localeName = parts[0] + '-' + parts.at(-1);

    // Convert to week info
    let weekInfo;
    try {
      weekInfo = new Intl.Locale(localeName).weekInfo;
    } catch (e) {
      // Ignore unofficial (zh_CN.GB2312) and breaking locales during development
      continue;
    }

    // To save bandwidth, we store fallback only for non-ISO-8601 weeks
    if (weekInfo.firstDay !== MONDAY || weekInfo.weekend[0] !== SATURDAY) {
      localeData[localeName] = weekInfo;
    }
  }
}

module.exports = localeData;
`;

const ISO_WEEK_INFO = {firstDay: 1, weekend: [6, 7]};

export function getWeekInfoForLocale(locale) {
  const weekInfo = WEEK_INFO[locale] ?? ISO_WEEK_INFO;
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
