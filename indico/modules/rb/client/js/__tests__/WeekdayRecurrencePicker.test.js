// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

describe('can localize shorthand weekday names, but can keep the values in English', () => {
  const cases = [
    {
      locale: 'de',
      expectedValues: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
      expectedTexts: ['Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.', 'So.'],
    },
    {
      locale: 'en-gb',
      expectedValues: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
      expectedTexts: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    },
    {
      locale: 'en-us',
      expectedValues: ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'],
      expectedTexts: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    },
    {
      locale: 'fr',
      expectedValues: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
      expectedTexts: ['lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.', 'dim.'],
    },
    {
      locale: 'pt-br',
      expectedValues: ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'],
      expectedTexts: ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'],
    },
    {
      locale: 'es',
      expectedValues: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
      expectedTexts: ['lun.', 'mar.', 'mié.', 'jue.', 'vie.', 'sáb.', 'dom.'],
    },
    {
      locale: 'it',
      expectedValues: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
      expectedTexts: ['lun', 'mar', 'mer', 'gio', 'ven', 'sab', 'dom'],
    },
    {
      locale: 'tr',
      expectedValues: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
      expectedTexts: ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'],
    },
    {
      locale: 'pl',
      expectedValues: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
      expectedTexts: ['pon', 'wt', 'śr', 'czw', 'pt', 'sob', 'ndz'],
    },
    {
      locale: 'mn',
      expectedValues: ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'],
      expectedTexts: ['Ням', 'Дав', 'Мяг', 'Лха', 'Пүр', 'Баа', 'Бям'],
    },
    {
      locale: 'uk',
      expectedValues: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
      expectedTexts: ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'нд'],
    },
    {
      locale: 'hu',
      expectedValues: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
      expectedTexts: ['hét', 'kedd', 'sze', 'csüt', 'pén', 'szo', 'vas'],
    },
    {
      locale: 'zh-cn',
      expectedValues: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
      expectedTexts: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    },
  ];

  cases.forEach(({locale, expectedValues, expectedTexts}) => {
    it(`should return correct mappings in ${locale}`, () => {
      const oldLocale = moment.locale();
      moment.locale(locale);

      const weekdayNames = moment.weekdays(true);
      const WEEKDAYS = weekdayNames.map((_, index) => {
        const firstDayOfWeek = moment.localeData().firstDayOfWeek();
        const dayNumber = (firstDayOfWeek + index) % 7;
        return {
          value: moment().day(dayNumber).locale('en').format('ddd').toLowerCase(),
          text: moment().day(dayNumber).format('ddd'),
        };
      });

      const texts = WEEKDAYS.map(wd => wd.text);
      const values = WEEKDAYS.map(wd => wd.value);

      expect(texts).toEqual(expectedTexts);
      expect(values).toEqual(expectedValues);
      moment.locale(oldLocale);
    });
  });
});
