// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import CustomElementBase from 'indico/custom_elements/_base';
import {focusLost} from 'indico/utils/composite-events';
import {
  DateRange,
  OpenDateRange,
  SparseDateRange,
  getToday,
  isSameDate,
  toDateString,
} from 'indico/utils/date';
import {formatDate} from 'indico/utils/date_format';
import {createDateParser} from 'indico/utils/date_parser';
import {getWeekInfoForLocale, getFirstDayOfWeek, getWeekdayNames} from 'indico/utils/l10n';
import * as positioning from 'indico/utils/positioning';
import {setNativeInputValue} from 'indico/utils/react_integration';
import {DelayedAutoToggleController} from 'indico/utils/timing';

import * as ds from './date_selection';

import './ind_date_picker.scss';

const DEFAULT_LOCALE = document.documentElement.dataset.canonicalLocale;
const KEYBOARD_MOVEMENT = {
  ArrowRight: 'nextday',
  ArrowLeft: 'previousday',
  ArrowDown: 'nextweek',
  ArrowUp: 'previousweek',
};
// States used when determining the next action in range picker
const START_NEEDED = 0;
const END_NEEDED = 1;
const BOTH_POPULATED = 2;

CustomElementBase.define(
  'ind-date-picker',
  class extends CustomElementBase {
    // Last value of the internal id used in the widgets
    static lastId = 0;

    static attributes = {
      min: Date, // Minimum selectable date (inclusive)
      max: Date, // Maximum selectable date (inclusive)
      format: String, // Date format
    };

    static observedAttributes = ['min', 'max'];

    get value() {
      return this.querySelector('input').value;
    }

    set value(value) {
      const input = this.querySelector('input');
      CustomElementBase.setValue(input, value ? formatDate(this.format, new Date(value)) : '');
      input.dispatchEvent(new Event('input', {bubbles: true}));
    }

    setup() {
      const indDatePicker = this;
      const id = `date-picker-${this.constructor.lastId++}`;
      const input = this.querySelector('input');
      const openCalendarButton = this.querySelector('button');
      const formatDescription = this.querySelector('[data-format]');
      const indCalendar = this.querySelector('ind-calendar');

      const parseDate = createDateParser(this.format);

      indCalendar.format = this.format;
      indCalendar.rangeStart = indCalendar.rangeEnd = toDateString(parseDate(this.value));
      formatDescription.id = `${id}-format`;
      input.setAttribute('aria-describedby', formatDescription.id);

      updateRange();

      // This property is defined here rather than in the class because it
      // relies on the parseDate() function created in this scope.
      Object.defineProperty(this, 'date', {
        get: () => parseDate(input.value),
      });

      openCalendarButton.addEventListener('click', () => {
        // Disable the button to prevent re-opening when clicking
        // the button while the dialog is open
        openCalendarButton.disabled = true;
        openDialog(indCalendar, input);
      });
      indCalendar.addEventListener('close', () => {
        openCalendarButton.disabled = false;
      });
      indCalendar.addEventListener('x-keyclose', () => {
        openCalendarButton.disabled = false;
        openCalendarButton.focus();
      });
      indCalendar.addEventListener('x-select', evt => {
        setValue(new Date(evt.target.value));
        indCalendar.open = false;
        input.select();
        input.focus();
      });
      input.addEventListener('keydown', evt => {
        if (evt.code === 'ArrowDown' && evt.altKey) {
          openDialog(indCalendar, input);
        }
      });
      input.addEventListener('input', () => {
        indCalendar.rangeStart = indCalendar.rangeEnd = toDateString(parseDate(this.value));
      });
      this.addEventListener('x-attrchange.min', updateRange);
      this.addEventListener('x-attrchange.max', updateRange);

      function setValue(date) {
        if (isSameDate(indDatePicker.date, date)) {
          return;
        }
        CustomElementBase.setValue(input, formatDate(indDatePicker.format, date));
        input.dispatchEvent(new Event('input', {bubbles: true}));
      }

      function updateRange() {
        indCalendar.setAllowableSelectionRange(
          new OpenDateRange(indDatePicker.min, indDatePicker.max)
        );
      }
    }
  }
);

CustomElementBase.define(
  'ind-date-range-picker',
  class extends CustomElementBase {
    // Last value of the internal id used in the widgets
    static lastId = 0;

    static attributes = {
      rangeStart: Date, // Start of the selected range (inclusive)
      rangeEnd: Date, // End of the selected range (inclusive)
      rangeStartMin: Date, // Minimum allowed value for the start of the range (inclusive)
      rangeStartMax: Date, // Maximum allowed value for the start of the range (inclusive)
      rangeEndMin: Date, // Minimum allowed value for the end of the range (inclusive)
      rangeEndMax: Date, // Minimum allowed value for the end of the range (inclusive)
    };

    static observedAttributes = [
      'range-start',
      'range-end',
      'range-start-min',
      'range-start-max',
      'range-end-min',
      'range-end-max',
    ];

    get value() {
      const rangeStartInput = this.querySelector('input[data-range-start]');
      const rangeEndInput = this.querySelector('input[data-range-end]');
      return `${rangeStartInput.value}:${rangeEndInput.value}`;
    }

    get selectionState() {
      if (!this.rangeStart) {
        return START_NEEDED;
      }

      if (!this.rangeEnd) {
        return END_NEEDED;
      }

      return BOTH_POPULATED;
    }

    get startRange() {
      return new OpenDateRange(this.rangeStartMin, this.rangeStartMax);
    }

    get endRange() {
      return new OpenDateRange(this.rangeEndMin, this.rangeEndMax);
    }

    get combinedRange() {
      return new SparseDateRange(this.startRange, this.endRange);
    }

    setup() {
      const indDateRangePicker = this;
      const id = `date-range-picker-${this.constructor.lastId++}`;
      const fieldset = this.querySelector('fieldset');
      const rangeStartInput = this.querySelector('input[data-range-start]');
      const rangeEndInput = this.querySelector('input[data-range-end]');
      const calendarTriggerLeft = this.querySelector('[data-calendar-trigger=left]');
      const calendarTriggerRight = this.querySelector('[data-calendar-trigger=right]');
      const formatDescription = this.querySelector('[data-format]');
      const indCalendar = this.querySelector('ind-calendar');

      const leftTriggerLocked = calendarTriggerLeft.disabled;
      const rightTriggerLocked = calendarTriggerRight.disabled;

      let selection = ds.newRangeSelection(
        this.rangeStart,
        this.rangeEnd,
        undefined,
        leftTriggerLocked,
        rightTriggerLocked
      );

      const dateFormat = formatDescription.textContent
        .split(':')[1]
        .trim()
        .toLowerCase();
      const parseDate = createDateParser(dateFormat);

      indCalendar.format = dateFormat;
      indCalendar.rangeStart = this.rangeStart;
      indCalendar.rangeEnd = this.rangeEnd;
      indCalendar.setSelectionPreview(selection);
      rangeStartInput.defaultValue = formatDate(dateFormat, this.rangeStart);
      rangeEndInput.defaultValue = formatDate(dateFormat, this.rangeEnd);
      updateSelectionLimits();

      formatDescription.id = `${id}-format`;
      rangeStartInput.setAttribute('aria-describedby', formatDescription.id);
      rangeEndInput.setAttribute('aria-describedby', formatDescription.id);

      // This property is defined here rather than in the class because it
      // relies on the parseDate() function created in this scope.
      Object.defineProperty(this, 'dateRange', {
        get: () => {
          return [parseDate(rangeStartInput.value), parseDate(rangeEndInput.value)];
        },
      });
      this.addEventListener('click', evt => {
        if (evt.target === evt.currentTarget || evt.target === fieldset) {
          rangeStartInput.focus();
          rangeStartInput.select();
        }
      });
      this.addEventListener('x-attrchange.range-start', () => {
        indCalendar.rangeStart = this.rangeStart;
        rangeStartInput.defaultValue = formatDate(dateFormat, this.rangeStart);
      });
      this.addEventListener('x-attrchange.range-end', () => {
        indCalendar.rangeEnd = this.rangeEnd;
        rangeEndInput.defaultValue = formatDate(dateFormat, this.rangeEnd);
      });
      this.addEventListener('x-attrchange.range-start-min', updateSelectionLimits);
      this.addEventListener('x-attrchange.range-start-max', updateSelectionLimits);
      this.addEventListener('x-attrchange.range-end-min', updateSelectionLimits);
      this.addEventListener('x-attrchange.range-end-max', updateSelectionLimits);
      rangeStartInput.addEventListener('input', () => {
        const date = parseDate(rangeStartInput.value);
        indCalendar.rangeStart = date;
        selection = selection.copy({left: date});
      });
      rangeEndInput.addEventListener('input', () => {
        const date = parseDate(rangeEndInput.value);
        indCalendar.rangeEnd = date;
        selection = selection.copy({right: date});
      });
      rangeStartInput.addEventListener('keydown', handleAltDownToOpen);
      rangeEndInput.addEventListener('keydown', handleAltDownToOpen);
      calendarTriggerLeft.addEventListener('click', () => {
        selection = ds.triggerLeft(selection);
        openCalendar();
      });
      calendarTriggerRight.addEventListener('click', () => {
        selection = ds.triggerRight(selection);
        openCalendar();
      });
      indCalendar.addEventListener('close', () => {
        calendarTriggerLeft.disabled = leftTriggerLocked;
        calendarTriggerRight.disabled = rightTriggerLocked;
      });
      indCalendar.addEventListener('x-select', evt => {
        const result = ds.select(selection, new Date(evt.target.value));
        selection = result.selection;

        // Close the calendar if needed
        if (result.close) {
          indCalendar.open = false;
        }

        // Set the input values where the value changed
        if (!isSameDate(selection.left, indCalendar.rangeStart)) {
          setNativeInputValue(rangeStartInput, formatDate(dateFormat, selection.left));
          rangeStartInput.dispatchEvent(new Event('input', {bubbles: true}));
        }
        if (!isSameDate(selection.right, indCalendar.rangeEnd)) {
          setNativeInputValue(rangeEndInput, formatDate(dateFormat, selection.right));
          rangeEndInput.dispatchEvent(new Event('change', {bubbles: true}));
        }

        // Update the selection preview and range restriction
        indCalendar.setSelectionPreview(selection);
        updateSelectionLimits();
      });

      function updateSelectionLimits() {
        if (selection.trigger === ds.LEFT) {
          indCalendar.setAllowableSelectionRange(indDateRangePicker.startRange);
        } else {
          indCalendar.setAllowableSelectionRange(indDateRangePicker.endRange);
        }
      }

      function openCalendar() {
        indCalendar.setSelectionPreview(selection);
        updateSelectionLimits();
        calendarTriggerLeft.disabled = true;
        calendarTriggerRight.disabled = true;
        openDialog(indCalendar, indDateRangePicker);
      }

      function handleAltDownToOpen(evt) {
        if (evt.code === 'ArrowDown' && evt.altKey) {
          openDialog(indCalendar, indDateRangePicker);
        }
      }
    }
  }
);

CustomElementBase.define(
  'ind-inline-date-picker',
  class extends CustomElementBase {
    static attributes = {
      value: Date,
    };

    static observedAttributes = ['value'];

    setup() {
      const indCalendar = this.querySelector('ind-calendar');
      let selection = ds.newSingleSelection(this.value, false, ds.SELECTION_SINGLE);

      indCalendar.setSelectionPreview(selection);
      indCalendar.rangeStart = this.value;
      indCalendar.rangeEnd = this.value;

      indCalendar.addEventListener('x-select', evt => {
        const result = ds.select(selection, new Date(evt.target.value));
        selection = result.selection;
        indCalendar.setSelectionPreview(selection);
        this.dispatchEvent(
          new CustomEvent('change', {
            bubbles: true,
            detail: {date: selection.date},
          })
        );
      });

      this.addEventListener('x-attrchange.value', () => {
        indCalendar.rangeStart = indCalendar.rangeEnd = this.value;
      });
    }
  }
);

CustomElementBase.define(
  'ind-inline-date-range-picker',
  class extends CustomElementBase {
    static attributes = {
      rangeStart: Date,
      rangeEnd: Date,
    };

    static observedAttributes = ['range-start', 'range-end'];

    setup() {
      const indCalendar = this.querySelector('ind-calendar');
      let selection = ds.newRangeSelection(
        this.rangeStart,
        this.rangeEnd,
        undefined,
        undefined,
        undefined,
        ds.SELECTION_SIMPLE_RANGE
      );

      indCalendar.setSelectionPreview(selection);

      indCalendar.addEventListener('x-select', evt => {
        const result = ds.select(selection, new Date(evt.target.value));
        selection = result.selection;
        indCalendar.setSelectionPreview(selection);
        if (selection.completed) {
          indCalendar.pausePreview();
        } else {
          indCalendar.resumePreview();
        }
        if (selection.getSelectionState() === ds.BOTH) {
          this.dispatchEvent(
            new CustomEvent('change', {
              bubbles: true,
              detail: {
                left: selection.left,
                right: selection.right,
              },
            })
          );
        }
      });
    }
  }
);

/**
 * Implements dialog mode events
 *
 * This class contains all behavior specific to the use of the <ind-calendar>
 * element within a dialog. For other use cases, provide a class of the identical
 * interface that implements different behavior.
 **/
class DialogModeController {
  constructor(calendar, options) {
    this.calendar = calendar;
    this.dialog = this.calendar.firstElementChild;
    this.options = options;
  }

  setUpEvents() {
    focusLost(this.dialog, () => {
      this.calendar.open = false;
    });
    // Handle closing/opening the dialog by clicking outside
    this.dialog.addEventListener('keydown', evt => {
      if (evt.code !== 'Escape') {
        return;
      }
      this.calendar.open = false;
      this.calendar.dispatchEvent(new Event('x-keyclose'));
    });
    // Handle dialog open/close initialized through the ind-calendar `open` attribute
    this.calendar.addEventListener('x-attrchange.open', () => {
      if (!this.dialog) {
        console.warn(
          'ind-calendar: Attempt to open or close dialog with no dialog element present'
        );
        return;
      }
      if (this.calendar.open) {
        if (this.dialog.open) {
          return;
        }
        this.options.onopen();
        this.dialog.show();
        this.dialog.focus();
        this.dialog.dispatchEvent(new Event('open', {bubbles: true}));
      } else {
        if (!this.dialog.open) {
          return;
        }
        this.dialog.close();
        this.options.onclose?.();
        this.dialog.dispatchEvent(new Event('close', {bubbles: true}));
      }
    });
  }

  setUpGlobalEvent() {
    this.abortController = new AbortController();

    // Note that this may not work on iOS Safari. We are not currently explicitly
    // targeting this browser, so we'll leave this as is.
    window.addEventListener(
      'click',
      evt => {
        if (!this.calendar.open) {
          return;
        }
        if (evt.target.closest('dialog') === this.dialog) {
          return;
        }
        setTimeout(() => {
          this.calendar.open = false;
        });
      },
      {signal: this.abortController.signal}
    );
  }

  tearDownGlobalEvents() {
    this.abortController.abort();
  }
}

/**
 * Implements inline mode events
 *
 * This is (currently) a dummy version of the dialog mode controller, which does
 * nothing at all. It is used for completely static calendars that don't wrap a
 * <dialog> element.
 */
class InlineModeController {
  setUpEvents() {}

  setUpGlobalEvents() {}

  tearDownGlobalEvents() {}
}

CustomElementBase.define(
  'ind-calendar',
  class extends CustomElementBase {
    static attributes = {
      open: Boolean,
      locale: {
        type: String,
        default: DEFAULT_LOCALE,
      },
      rangeStart: Date,
      rangeEnd: Date,
    };

    static observedAttributes = ['range-start', 'range-end', 'open'];

    constructor() {
      super();
      this.allowableSelectionRange = new OpenDateRange();
      this.previewPaused = false;
      this.previewToggleController = new DelayedAutoToggleController(
        () => {
          this.previewPaused = true;
        },
        () => {
          this.previewPaused = false;
        },
        3000
      );
    }

    setAllowableSelectionRange(dateRange) {
      this.allowableSelectionRange = dateRange;
      this.dispatchEvent(new Event('x-rangechange'));
    }

    setSelectionPreview(selection) {
      this.selectionPreview = selection.copy();
    }

    pausePreview() {
      this.previewToggleController.activate();
    }

    resumePreview() {
      this.previewToggleController.reset();
    }

    setup() {
      let calendarDisplayDate, hoverCursor;

      const indCalendar = this;
      const BehaviorController =
        this.firstElementChild.tagName === 'DIALOG' ? DialogModeController : InlineModeController;
      const behaviorController = new BehaviorController(this, {
        onclose: () => {
          calendarDisplayDate = undefined;
          updateCalendar();
        },
        onopen: () => {
          calendarDisplayDate = undefined;
          updateCalendar();
        },
      });
      const monthYearGroup = this.querySelector('.month-year');
      const editMonthSelect = monthYearGroup.querySelector('select');
      const editYearInput = monthYearGroup.querySelector('input');
      const calendars = this.querySelector('.calendars');
      const dateGrids = this.querySelectorAll('ind-date-grid');

      // Populate month names in the select list
      for (let i = 0; i < 12; i++) {
        const date = new Date();
        date.setDate(1);
        date.setMonth(i);
        const monthName = date.toLocaleDateString(this.locale, {month: 'short'});
        const monthOption = document.createElement('option');
        monthOption.value = i;
        monthOption.textContent = monthName;
        editMonthSelect.append(monthOption);
      }
      // Populate year
      editYearInput.value = new Date().getFullYear();

      for (const grid of dateGrids) {
        grid.hideDatesFromOtherMonths = dateGrids.length > 1;
      }

      this.addEventListener('x-attrchange.range-start', updateCalendar);
      this.addEventListener('x-attrchange.range-end', updateCalendar);
      this.addEventListener('x-rangechange', updateCalendar);

      behaviorController.setUpEvents();

      // Handle calendar interaction
      indCalendar.addEventListener('click', evt => {
        const button = evt.target.closest('button[value]');
        if (!button) {
          return;
        }
        switch (button.value) {
          case 'previous-year':
            calendarDisplayDate.setFullYear(calendarDisplayDate.getFullYear() - 1);
            updateCalendar();
            break;
          case 'next-year':
            calendarDisplayDate.setFullYear(calendarDisplayDate.getFullYear() + 1);
            updateCalendar();
            break;
          case 'previous-month':
            calendarDisplayDate.setMonth(calendarDisplayDate.getMonth() - 1);
            updateCalendar();
            break;
          case 'next-month':
            calendarDisplayDate.setMonth(calendarDisplayDate.getMonth() + 1);
            updateCalendar();
            break;
          default:
            // The only remaining option is a calendar button - date selection.
            // We dispatch the x-select event on the button itself, and the
            // input component will handle updating its value.
            if (button.hasAttribute('aria-disabled')) {
              return;
            }
            button.dispatchEvent(new Event('x-select', {bubbles: true}));
        }
      });
      editYearInput.addEventListener('input', () => {
        const year = parseInt(editYearInput.value, 10);
        if (isNaN(year)) {
          editYearInput.reportValidity();
          return;
        }
        calendarDisplayDate.setFullYear(year);
        updateCalendar();
      });
      editMonthSelect.addEventListener('change', () => {
        calendarDisplayDate.setMonth(editMonthSelect.value);
        updateCalendar();
      });

      // Grid calendar month change
      indCalendar.addEventListener('x-datechange.next', () => {
        calendarDisplayDate.setMonth(calendarDisplayDate.getMonth() + 1);
        updateCalendar();
      });
      indCalendar.addEventListener('x-datechange.previous', () => {
        calendarDisplayDate.setMonth(calendarDisplayDate.getMonth() - 1);
        updateCalendar();
      });

      // Grid cursor movement
      indCalendar.addEventListener('x-move', evt => {
        const {direction, currentDate} = evt.detail;
        const nextDate = new Date(currentDate);

        switch (direction) {
          case 'nextday':
            nextDate.setDate(nextDate.getDate() + 1);
            break;
          case 'previousday':
            nextDate.setDate(nextDate.getDate() - 1);
            break;
          case 'nextweek':
            nextDate.setDate(nextDate.getDate() + 7);
            break;
          case 'previousweek':
            nextDate.setDate(nextDate.getDate() - 7);
            break;
        }

        const nextDateString = nextDate.toDateString();
        const targetButton = findFocusableButton(nextDateString);
        if (targetButton) {
          targetButton.focus();
        } else {
          if (direction.startsWith('next')) {
            calendarDisplayDate.setMonth(calendarDisplayDate.getMonth() + 1);
            updateCalendar();
          } else {
            calendarDisplayDate.setMonth(calendarDisplayDate.getMonth() - 1);
            updateCalendar();
          }
          setTimeout(() => {
            findFocusableButton(nextDateString).focus();
          });
        }
      });

      calendars?.addEventListener('focusin', evt => {
        if (evt.target.matches('[aria-disabled]')) {
          return;
        }
        hoverCursor = evt.target.value;
        updateGrids();
      });
      calendars?.addEventListener('focusout', () => {
        hoverCursor = undefined;
        updateGrids();
      });
      calendars?.addEventListener('mouseover', evt => {
        if (evt.target.matches('button[value]:not([aria-disabled])')) {
          hoverCursor = evt.target.value;
          updateGrids();
        }
      });
      calendars?.addEventListener('mouseout', () => {
        hoverCursor = undefined;
        updateGrids();
      });

      function getSelectionRange() {
        return new DateRange(indCalendar.rangeStart, indCalendar.rangeEnd);
      }

      function getHoverRange() {
        // A component that wishes to display the preview must set
        // the `selectionPreview` property by calling `setSelectionPreview()`
        // on the <ind-calendar> element and the value must be a `Selection`
        // object (see `date_selection.js`).
        //
        // When no valid preview can be created, or the preview is paused
        // an empty `DateRange` is returned.

        if (!indCalendar.selectionPreview || indCalendar.previewPaused) {
          return new DateRange();
        }

        // Obtain the cursor position
        const cursorDate = hoverCursor && new Date(hoverCursor);
        if (!cursorDate) {
          return new DateRange();
        }

        // Create a preview
        const {selection: preview} = ds.select(indCalendar.selectionPreview, cursorDate);
        return preview.toDateRange();
      }

      function updateCalendar() {
        const selectedRange = getSelectionRange();
        const firstDayOfMonth = new Date(
          calendarDisplayDate ||
            selectedRange.start ||
            indCalendar.allowableSelectionRange.start ||
            getToday()
        );
        firstDayOfMonth.setDate(1);

        // If the calendar display date is not set, set it to the computed
        // first day of month
        calendarDisplayDate ??= firstDayOfMonth;

        // Populate the year/month controls

        monthYearGroup.querySelector('select').value = firstDayOfMonth.getMonth();
        editYearInput.value = firstDayOfMonth.getFullYear();

        // Populate the calendar cells
        updateGrids(firstDayOfMonth.getFullYear(), firstDayOfMonth.getMonth());
      }

      function updateGrids(year, month) {
        const selectionRange = getSelectionRange();
        const hoverRange = getHoverRange();
        const markedRange = hoverRange.isInvalid ? selectionRange : hoverRange;
        dateGrids.forEach((grid, i) => {
          if (year !== undefined && month !== undefined) {
            const gridDate = new Date(year, month);
            gridDate.setMonth(gridDate.getMonth() + i);
            grid.year = gridDate.getFullYear();
            grid.month = gridDate.getMonth();
          }
          grid.rangeStart = markedRange.start?.toString() || '';
          grid.rangeEnd = markedRange.end?.toString() || '';
          grid.setAllowableSelectionRange(indCalendar.allowableSelectionRange);
        });
      }

      function findFocusableButton(dateString) {
        const focusableButtons = [];
        for (const grid of dateGrids) {
          const button = grid.makeFocusable(dateString);
          if (button) {
            focusableButtons.push(button);
          }
        }
        return (
          focusableButtons.find(button => button.dataset.currentMonth === 'true') ||
          focusableButtons[0]
        );
      }
    }
  }
);

CustomElementBase.define(
  'ind-date-grid',
  class extends CustomElementBase {
    static lastId = 0;

    static attributes = {
      rangeStart: Date,
      rangeEnd: Date,
      year: Number,
      month: Number,
      locale: {
        type: String,
        default: DEFAULT_LOCALE,
      },
      hideDatesFromOtherMonths: Boolean,
    };

    static observedAttributes = ['year', 'month', 'range-start', 'range-end'];

    constructor() {
      super();
      this.allowableSelectionRange = new OpenDateRange();
    }

    setAllowableSelectionRange(range) {
      this.allowableSelectionRange = range;
      this.dispatchEvent(new Event('x-rangechange'));
    }

    setup() {
      const indDateGrid = this;
      const weekInfo = getWeekInfoForLocale(this.locale);
      const listbox = this.querySelector('[role=listbox]');
      const calendarButtons = listbox.querySelectorAll('[role=option]');
      const weekdayLabels = this.querySelectorAll('[data-weekday-labels] abbr');
      const monthLabel = this.querySelector('[data-month-label]');
      const id = `date-grid-${this.constructor.lastId++}`;

      // Populate weekday names in the calendar header
      getWeekdayNames(weekInfo, this.locale).forEach(({full, short, isWeekend}, i) => {
        const headerCell = weekdayLabels[i];
        headerCell.setAttribute('aria-label', full);
        headerCell.setAttribute('title', full);
        headerCell.textContent = short;
        headerCell.toggleAttribute('data-weekend', isWeekend);
        headerCell.id = `${id}-wkd-${i + 1}`;
      });

      // Prepare the initial button states
      calendarButtons.forEach((calendarButton, i) => {
        calendarButton.setAttribute('aria-describedby', weekdayLabels[i % 7].id);
        calendarButton.tabIndex = -1;
        calendarButton.type = 'button';
      });

      indDateGrid.addEventListener('x-attrchange', updateGridDates);

      listbox.addEventListener('keydown', evt => {
        // Movement keyboard commands simply translate the keyboard
        // events to custom x-move events. These are handled by
        // <ind-calendar> because that's the first common ancestor
        // of all the grids, and can facilitate cross-grid movement.

        const currentDate = listbox.querySelector(':focus').value;

        const movementDirection = KEYBOARD_MOVEMENT[evt.code];
        if (movementDirection) {
          evt.preventDefault();
          indDateGrid.dispatchEvent(
            new CustomEvent('x-move', {
              detail: {direction: movementDirection, currentDate},
              bubbles: true,
            })
          );
        }
      });

      let debounceTimer;

      function updateGridDates() {
        // This function is debounced as sometimes we may set multiple
        // properties on the ind-date-grid element, and we only want the
        // DOM to update once.
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          const firstDayOfMonth = new Date(indDateGrid.year, indDateGrid.month, 1);
          const firstDayOfCalendar = getFirstDayOfWeek(weekInfo, firstDayOfMonth);
          const calendarMonth = firstDayOfMonth.getMonth();

          if (monthLabel) {
            monthLabel.textContent = firstDayOfMonth.toLocaleDateString(indDateGrid.locale, {
              month: 'long',
              year: 'numeric',
            });
          }

          const selectedRange = new DateRange(indDateGrid.rangeStart, indDateGrid.rangeEnd);

          calendarButtons.forEach((calendarButton, i) => {
            const date = new Date(firstDayOfCalendar);
            date.setDate(date.getDate() + i);
            const belongsToCurrentMonth = date.getMonth() === calendarMonth;
            const isRenderable = !indDateGrid.hideDatesFromOtherMonths || belongsToCurrentMonth;

            calendarButton.dataset.currentMonth = belongsToCurrentMonth;
            calendarButton.disabled = !isRenderable;

            if (!isRenderable) {
              calendarButton.textContent = '';
              calendarButton.removeAttribute('aria-label');
              calendarButton.removeAttribute('aria-selected');
              calendarButton.removeAttribute('data-week');
              calendarButton.removeAttribute('data-range-start');
              calendarButton.removeAttribute('data-range-end');
              calendarButton.value = '';
              calendarButton.tabIndex = -1;
              calendarButton.disabled = true;
              return;
            }

            // Update button attributes
            calendarButton.textContent = date.getDate();
            calendarButton.setAttribute(
              'aria-label',
              date.toLocaleDateString(indDateGrid.locale, {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })
            );
            calendarButton.toggleAttribute(
              'data-weekend',
              weekInfo.weekend.includes(date.getDay() + 1)
            );
            calendarButton.tabIndex = -1;
            calendarButton.value = toDateString(date);

            if (this.allowableSelectionRange.includes(date)) {
              calendarButton.removeAttribute('aria-disabled');
            } else {
              calendarButton.setAttribute('aria-disabled', true);
            }

            if (selectedRange.includes(date)) {
              calendarButton.setAttribute('aria-selected', true);
            } else {
              calendarButton.removeAttribute('aria-selected');
            }
            calendarButton.toggleAttribute('data-range-start', selectedRange.startsWith(date));
            calendarButton.toggleAttribute('data-range-end', selectedRange.endsWith(date));
          });

          const focusableButton = listbox.querySelector(
            '[role=option]:is([aria-selected=true],[data-current-month=true]:not([aria-disabled]))'
          );
          if (focusableButton) {
            focusableButton.tabIndex = 0;
          }
          indDateGrid.dispatchEvent(new Event('x-update-grid'));
        });
      }
    }

    makeFocusable(dateString) {
      const calendarButton = this.querySelector(`[value="${dateString}"]`);
      if (!calendarButton) {
        return;
      }
      const currentlyFocusable = this.querySelector('[tabindex="0"]');
      if (currentlyFocusable) {
        currentlyFocusable.tabIndex = -1;
      }
      calendarButton.tabIndex = 0;
      return calendarButton;
    }
  }
);

function openDialog(indCalendar, anchor) {
  const stopPositioning = positioning.position(
    indCalendar.firstElementChild,
    anchor,
    positioning.dropdownPositionStrategy,
    () => {
      indCalendar.open = true;
    }
  );
  indCalendar.querySelector('dialog').addEventListener('close', stopPositioning, {once: true});
}
