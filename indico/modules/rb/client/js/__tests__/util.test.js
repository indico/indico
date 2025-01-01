// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

import {renderRecurrenceWeekdays} from '../util';

describe('can render the recurrence weekdays', () => {
  it('should return null if weekdays array is empty', () => {
    const weekdays = [];
    expect(renderRecurrenceWeekdays({weekdays})).toBeNull();
  });

  it('should return null if weekdays array is null', () => {
    const weekdays = null;
    expect(renderRecurrenceWeekdays({weekdays})).toBeNull();
  });

  it('should handle a single unknown/bad weekday', () => {
    const weekdays = ['xyz'];
    expect(renderRecurrenceWeekdays({weekdays})).toBeNull();
  });

  it('should handle multiple unknown/bad weekdays', () => {
    const weekdays = ['xyz', 'abc', 'def'];
    expect(renderRecurrenceWeekdays({weekdays})).toBeNull();
  });

  it('correctly formats a single weekday', () => {
    const formatted = renderRecurrenceWeekdays({weekdays: ['mon']});
    expect(formatted).toBe('Every Monday');
  });

  it('correctly formats two weekdays', () => {
    const formatted = renderRecurrenceWeekdays({weekdays: ['mon', 'tue']});
    expect(formatted).toBe('Every Monday and Tuesday');
  });

  it('correctly formats multiple weekdays', () => {
    const formatted = renderRecurrenceWeekdays({weekdays: ['mon', 'tue', 'wed']});
    expect(formatted).toBe('Every Monday, Tuesday, and Wednesday');
  });

  it('correctly formats weekdays in non-sequential order', () => {
    const formatted = renderRecurrenceWeekdays({weekdays: ['wed', 'mon', 'fri']});
    expect(formatted).toBe('Every Monday, Wednesday, and Friday');
  });

  it('should handle all weekdays', () => {
    const weekdays = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
    const expected = 'Every Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, and Sunday';
    expect(renderRecurrenceWeekdays({weekdays})).toBe(expected);
  });

  it('should handle all weekdays in non-sequential order', () => {
    const weekdays = ['wed', 'mon', 'fri', 'tue', 'sun', 'thu', 'sat'];
    const expected = 'Every Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, and Sunday';
    expect(renderRecurrenceWeekdays({weekdays})).toBe(expected);
  });
});

describe('can render only the recurrence weekdays (short format)', () => {
  it('should handle a single weekday', () => {
    const weekdays = ['mon'];
    expect(renderRecurrenceWeekdays({weekdays, weekdaysOnly: true})).toBe('Monday');
  });

  it('should handle multiple weekdays', () => {
    const weekdays = ['mon', 'tue', 'wed'];
    expect(renderRecurrenceWeekdays({weekdays, weekdaysOnly: true})).toBe(
      'Monday, Tuesday, and Wednesday'
    );
  });

  it('should handle all weekdays', () => {
    const weekdays = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
    const expected = 'Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, and Sunday';
    expect(renderRecurrenceWeekdays({weekdays, weekdaysOnly: true})).toBe(expected);
  });
});

describe('can render the recurrence weekdays whilst taking the locale into account', () => {
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
    ['hu', 'hétfő, kedd, szerda, csütörtök, péntek, szombat és vasárnap'],
    ['zh-cn', '星期一、星期二、星期三、星期四、星期五、星期六和星期日'],
  ];

  test.each(cases)(
    'should localize all weekdays in non-sequential order in %s',
    (locale, expected) => {
      const oldLocale = moment.locale();
      moment.locale(locale);
      const formatted = renderRecurrenceWeekdays({weekdays: unorderedWeekdays});
      expect(formatted).toBe(`Every ${expected}`);
      moment.locale(oldLocale);
    }
  );
});

describe('can render the recurrence weekdays with support for repetition', () => {
  it('should handle a single weekday with a repetition', () => {
    const weekdays = ['mon'];
    const repetition = 2;
    const expected = 'Every 2 weeks on Monday';
    expect(renderRecurrenceWeekdays({weekdays, repetition})).toBe(expected);
  });

  it('should handle multiple weekdays with a repetition', () => {
    const weekdays = ['mon', 'tue', 'wed'];
    const repetition = 3;
    const expected = 'Every 3 weeks on Monday, Tuesday, and Wednesday';
    expect(renderRecurrenceWeekdays({weekdays, repetition})).toBe(expected);
  });

  it('should handle all weekdays with a repetition', () => {
    const weekdays = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
    const repetition = 4;
    const expected =
      'Every 4 weeks on Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, and Sunday';
    expect(renderRecurrenceWeekdays({weekdays, repetition})).toBe(expected);
  });

  it('should handle all weekdays in non-sequential order with a repetition', () => {
    const weekdays = ['wed', 'mon', 'fri', 'tue', 'sun', 'thu', 'sat'];
    const repetition = 5;
    const expected =
      'Every 5 weeks on Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, and Sunday';
    expect(renderRecurrenceWeekdays({weekdays, repetition})).toBe(expected);
  });
});

describe('can render the recurrence weekdays with support for repetitions whilst taking the locale into account', () => {
  const unorderedWeekdays = ['wed', 'mon', 'fri', 'tue', 'sun', 'thu', 'sat'];
  const repetition = 3;
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
    ['hu', 'hétfő, kedd, szerda, csütörtök, péntek, szombat és vasárnap'],
    ['zh-cn', '星期一、星期二、星期三、星期四、星期五、星期六和星期日'],
  ];

  test.each(cases)(
    'should localize all weekdays in non-sequential order in %s with an repetition',
    (locale, expected) => {
      const oldLocale = moment.locale();
      moment.locale(locale);
      const formatted = renderRecurrenceWeekdays({weekdays: unorderedWeekdays, repetition});
      expect(formatted).toBe(`Every 3 weeks on ${expected}`);
      moment.locale(oldLocale);
    }
  );
});
