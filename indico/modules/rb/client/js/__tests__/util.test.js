// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

import {renderRecurrenceWeekdays} from '../util';

describe('renderRecurrenceWeekdays', () => {
  it('should return null if weekdays array is empty', () => {
    const weekdays = [];
    expect(renderRecurrenceWeekdays(weekdays)).toBeNull();
  });

  it('should return null if weekdays array is null', () => {
    const weekdays = null;
    expect(renderRecurrenceWeekdays(weekdays)).toBeNull();
  });

  it('should handle a single unknown/bad weekday', () => {
    const weekdays = ['xyz'];
    expect(renderRecurrenceWeekdays(weekdays)).toBeNull();
  });

  it('should handle multiple unknown/bad weekdays', () => {
    const weekdays = ['xyz', 'abc', 'def'];
    expect(renderRecurrenceWeekdays(weekdays)).toBeNull();
  });

  it('correctly formats a single weekday', () => {
    const formatted = renderRecurrenceWeekdays(['mon']);
    expect(formatted).toBe('Monday');
  });

  it('correctly formats two weekdays', () => {
    const formatted = renderRecurrenceWeekdays(['mon', 'tue']);
    expect(formatted).toBe('Monday and Tuesday');
  });

  it('correctly formats multiple weekdays', () => {
    const formatted = renderRecurrenceWeekdays(['mon', 'tue', 'wed']);
    expect(formatted).toBe('Monday, Tuesday, and Wednesday');
  });

  it('correctly formats weekdays in non-sequential order', () => {
    const formatted = renderRecurrenceWeekdays(['wed', 'mon', 'fri']);
    expect(formatted).toBe('Monday, Wednesday, and Friday');
  });

  it('should handle all weekdays', () => {
    const weekdays = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
    const expected = 'Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, and Sunday';
    expect(renderRecurrenceWeekdays(weekdays)).toBe(expected);
  });

  it('should handle all weekdays in non-sequential order', () => {
    const weekdays = ['wed', 'mon', 'fri', 'tue', 'sun', 'thu', 'sat'];
    const expected = 'Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, and Sunday';
    expect(renderRecurrenceWeekdays(weekdays)).toBe(expected);
  });
});

describe('renderLocalizedRecurrenceWeekdays', () => {
  const unorderedWeekdays = ['wed', 'mon', 'fri', 'tue', 'sun', 'thu', 'sat'];
  const cases = [
    ['de', 'Montag, Dienstag, Mittwoch, Donnerstag, Freitag, Samstag und Sonntag'],
    ['en-gb', 'Monday, Tuesday, Wednesday, Thursday, Friday, Saturday and Sunday'],
    ['en-us', 'Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, and Sunday'],
    ['fr', 'lundi, mardi, mercredi, jeudi, vendredi, samedi et dimanche'],
    [
      'pt-br',
      'segunda-feira, terça-feira, quarta-feira, quinta-feira, sexta-feira, sábado e domingo',
    ],
    ['es', 'lunes, martes, miércoles, jueves, viernes, sábado y domingo'],
    ['it', 'lunedì, martedì, mercoledì, giovedì, venerdì, sabato e domenica'],
    ['tr', 'Pazartesi, Salı, Çarşamba, Perşembe, Cuma, Cumartesi ve Pazar'],
    ['pl', 'poniedziałek, wtorek, środa, czwartek, piątek, sobota i niedziela'],
    ['mn', 'Даваа, Мягмар, Лхагва, Пүрэв, Баасан, Бямба, Ням'],
    ['uk', 'понеділок, вівторок, середа, четвер, п’ятниця, субота і неділя'],
    ['zh-cn', '星期一、星期二、星期三、星期四、星期五、星期六和星期日'],
  ];

  test.each(cases)(
    'should localize all weekdays in non-sequential order in %s',
    (locale, expected) => {
      const oldLocale = moment.locale();
      moment.locale(locale);
      const formatted = renderRecurrenceWeekdays(unorderedWeekdays);
      expect(formatted).toBe(expected);
      moment.locale(oldLocale);
    }
  );
});
