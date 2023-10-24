// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

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
