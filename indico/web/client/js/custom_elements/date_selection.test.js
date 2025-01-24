// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {DateRange} from 'indico/utils/date';

import * as ds from './date_selection';

describe('date_selection', () => {
  const assertResult = (result, range, close = false) => {
    expect(result.selection.toDateRange().toString()).toBe(new DateRange(...range).toString());
    expect(result.close).toBe(close);
  };

  it('should not apply any selection if trigger is not active', () => {
    const s = ds.newRangeSelection();

    const res = ds.select(s, new Date('Apr 24 2024'));

    expect(res).toEqual({close: true, selection: s});
  });

  it.each([
    [new Date('Jan 2 1982')],
    [new Date('Apr 24 2024')],
    [new Date()],
    [new Date('Jan 12 2088')],
  ])(
    'should select a date like %s as left there is no selection regardless of the trigger',
    selectedDate => {
      {
        // left
        const s = ds.newRangeSelection();

        const s1 = ds.triggerLeft(s);
        const result = ds.select(s1, selectedDate);

        assertResult(result, [selectedDate, undefined]);
      }

      {
        // right
        const s = ds.newRangeSelection();

        const s1 = ds.triggerRight(s);
        const result = ds.select(s1, selectedDate);

        assertResult(result, [selectedDate, undefined]);
      }
    }
  );

  it.each([
    [new Date('Jan 2 1982')],
    [new Date('Apr 24 2024')],
    [new Date()],
    [new Date('Jan 12 2088')],
  ])('should not clear the date when the same date is selected twice', selectedDate => {
    {
      // left
      const s = ds.newRangeSelection();

      const s1 = ds.triggerLeft(s);
      const {selection: s2} = ds.select(s1, selectedDate);
      const result = ds.select(s2, selectedDate);

      assertResult(result, [selectedDate, selectedDate], true);
    }

    {
      // right
      const s = ds.newRangeSelection();

      const s1 = ds.triggerRight(s);
      const {selection: s2} = ds.select(s1, selectedDate);
      const result = ds.select(s2, selectedDate);

      assertResult(result, [selectedDate, selectedDate], true);
    }
  });

  it.each([
    [new Date('Jan 2 1982')],
    [new Date('Apr 24 2024')],
    [new Date()],
    [new Date('Jan 12 2088')],
  ])(
    'should not clear the opposite when a date like %s is selected, regardless of the trigger',
    selectedDate => {
      {
        // left then right
        const s = ds.newRangeSelection(selectedDate);

        const s1 = ds.triggerRight(s);
        const result = ds.select(s1, selectedDate);

        assertResult(result, [selectedDate, selectedDate], true);
      }

      {
        // right then left
        const s = ds.newRangeSelection(undefined, selectedDate);

        const s1 = ds.triggerLeft(s);
        const result = ds.select(s1, selectedDate);

        assertResult(result, [selectedDate, selectedDate], true);
      }
    }
  );

  it('should move the selection if the left date is selected and an earlier date is selected afterwards', () => {
    const s = ds.newRangeSelection(new Date('Apr 24 2024'));

    const s1 = ds.triggerLeft(s);
    const result = ds.select(s1, new Date('Apr 12 2024'));

    assertResult(result, [new Date('Apr 12 2024'), undefined]);
  });

  it('should move the selection when left date is selected and left trigger is used again to set the left date', () => {
    const s = ds.newRangeSelection(new Date('Apr 24 2024'));

    const s1 = ds.triggerLeft(s);
    const result = ds.select(s1, new Date('Apr 29 2024'));

    assertResult(result, [new Date('Apr 29 2024'), undefined]);
    expect(result.selection.trigger).toBe(ds.RIGHT);
  });

  it('should clear the selection and select left if the right date is selected and a later date is selected afterwards', () => {
    const s = ds.newRangeSelection(undefined, new Date('Apr 24 2024'));

    const s1 = ds.triggerRight(s);
    const result = ds.select(s1, new Date('Apr 29 2024'));

    assertResult(result, [new Date('Apr 29 2024'), undefined]);
  });

  it('should move the selection if the right date is selected and then the right trigger is used to set an earlier date', () => {
    const s = ds.newRangeSelection(undefined, new Date('Apr 24 2024'));

    const s1 = ds.triggerRight(s);
    const result = ds.select(s1, new Date('Apr 12 2024'));

    assertResult(result, [undefined, new Date('Apr 12 2024')], true);
  });

  it('should select both ends of the range if the left trigger is used and then two dates are selected where second date is later', () => {
    const s = ds.newRangeSelection();

    const s1 = ds.triggerLeft(s);
    const {selection: s2} = ds.select(s1, new Date('Apr 24 2024'));
    const result = ds.select(s2, new Date('Apr 29 2024'));

    assertResult(result, [new Date('Apr 24 2024'), new Date('Apr 29 2024')], true);
  });

  it('should select the left date if right date is already selected and left trigger is used to select an earlier date', () => {
    const s = ds.newRangeSelection(undefined, new Date('Apr 24 2024'));

    const s1 = ds.triggerLeft(s);
    const result = ds.select(s1, new Date('Apr 12 2024'));

    assertResult(result, [new Date('Apr 12 2024'), new Date('Apr 24 2024')], true);
  });

  it('should move the left selection if both ends are selected and left trigger is used to set a date earlier than left', () => {
    const s = ds.newRangeSelection(new Date('Apr 24 2024'), new Date('Apr 29 2024'));

    const s1 = ds.triggerLeft(s);
    const result = ds.select(s1, new Date('Apr 19 2024'));

    assertResult(result, [new Date('Apr 19 2024'), new Date('Apr 29 2024')]);
    expect(result.selection.trigger).toBe(ds.RIGHT);
  });

  it('should clear the right date if both dates are selected and left trigger is used to select a date that is later than the right date', () => {
    const s = ds.newRangeSelection(new Date('Apr 24 2024'), new Date('Apr 29 2024'));

    const s1 = ds.triggerLeft(s);
    const result = ds.select(s1, new Date('May 2 2024'));

    assertResult(result, [new Date('May 2 2024'), undefined]);
  });

  it('should move the right date if both dates are selected and right trigger is used to select a date later than the left', () => {
    const s = ds.newRangeSelection(new Date('Apr 24 2024'), new Date('Apr 29 2024'));

    const s1 = ds.triggerRight(s);
    const result = ds.select(s1, new Date('Apr 27 2024'));

    assertResult(result, [new Date('Apr 24 2024'), new Date('Apr 27 2024')], true);
  });

  it('should select the left date and clear the right date if both dates are selected and the right trigger is used to select a date earlier than left', () => {
    const s = ds.newRangeSelection(new Date('Apr 24 2024'), new Date('Apr 29 2024'));

    const s1 = ds.triggerRight(s);
    const result = ds.select(s1, new Date('Apr 12 2024'));

    assertResult(result, [new Date('Apr 12 2024'), undefined]);
  });

  it('should copy an existing instance', () => {
    const s = ds.newRangeSelection(new Date('Apr 12 2024'), new Date('Apr 29 2024'), ds.LEFT);

    const s1 = s.copy();

    expect(s1).not.toBe(s);
    expect(s1.toDateRange().toString()).toBe(s.toDateRange().toString());
    expect(s1.trigger).toBe(s.trigger);
  });
});
