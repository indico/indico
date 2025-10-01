// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

describe('can localize shorthand weekday names, but can keep the values in English', () => {
  let oldLocale = null;

  beforeEach(() => {
    oldLocale = moment.locale();
  });

  afterEach(() => {
    moment.locale(oldLocale);
  });

  describe.each`
    locale     | expectedValues                                       | expectedTexts
    ${'de'}    | ${['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']} | ${['Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.', 'So.']}
    ${'en-gb'} | ${['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']} | ${['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}
    ${'en-us'} | ${['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']} | ${['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']}
    ${'fr'}    | ${['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']} | ${['lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.', 'dim.']}
    ${'pt-br'} | ${['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']} | ${['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb']}
    ${'es'}    | ${['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']} | ${['lun.', 'mar.', 'mié.', 'jue.', 'vie.', 'sáb.', 'dom.']}
    ${'it'}    | ${['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']} | ${['lun', 'mar', 'mer', 'gio', 'ven', 'sab', 'dom']}
    ${'tr'}    | ${['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']} | ${['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']}
    ${'pl'}    | ${['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']} | ${['pon', 'wt', 'śr', 'czw', 'pt', 'sob', 'ndz']}
    ${'mn'}    | ${['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']} | ${['Ням', 'Дав', 'Мяг', 'Лха', 'Пүр', 'Баа', 'Бям']}
    ${'uk'}    | ${['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']} | ${['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'нд']}
    ${'hu'}    | ${['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']} | ${['hét', 'kedd', 'sze', 'csüt', 'pén', 'szo', 'vas']}
    ${'zh-cn'} | ${['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']} | ${['周一', '周二', '周三', '周四', '周五', '周六', '周日']}
  `('should return correct mappings in $locale', ({locale, expectedValues, expectedTexts}) => {
    it(`Localized Text:      ${expectedTexts}
        Weekday Values (en): ${expectedValues}
    `, () => {
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
    });
  });
});
