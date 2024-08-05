// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import CustomElementBase from 'indico/custom_elements/_base';
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

customElements.define(
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
      indCalendar.min = this.min;
      indCalendar.max = this.max;
      formatDescription.id = `${id}-format`;
      input.setAttribute('aria-describedby', formatDescription.id);

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

customElements.define(
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
      let selection = ds.newSelection(this.rangeStart, this.rangeEnd);

      const dateFormat = formatDescription.textContent
        .split(':')[1]
        .trim()
        .toLowerCase();
      const parseDate = createDateParser(dateFormat);

      indCalendar.format = dateFormat;
      indCalendar.rangeStart = this.rangeStart;
      indCalendar.rangeEnd = this.rangeEnd;
      indCalendar.selectionPreview = selection.copy();
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
        calendarTriggerLeft.disabled = false;
        calendarTriggerRight.disabled = false;
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

        // Update the selection range restriction
        indCalendar.selectionPreview = selection.copy();
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
        indCalendar.selectionPreview = selection.copy();
        updateSelectionLimits();
        calendarTriggerLeft.disabled = true;
        calendarTriggerRight.disabled = true;
        openDialog(indCalendar, rangeStartInput);
      }

      function handleAltDownToOpen(evt) {
        if (evt.code === 'ArrowDown' && evt.altKey) {
          openDialog(indCalendar, rangeStartInput);
        }
      }
    }
  }
);

customElements.define(
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

    constructor() {
      super();
      this.allowableSelectionRange = new OpenDateRange();
    }

    setAllowableSelectionRange(dateRange) {
      this.allowableSelectionRange = dateRange;
      this.dispatchEvent(new Event('x-rangechange'));
    }

    setup() {
      const indCalendar = this;
      const dialog = this.firstElementChild;
      const monthYearGroup = this.querySelector('.month-year');
      const editMonthSelect = monthYearGroup.querySelector('select');
      const editYearInput = monthYearGroup.querySelector('input');
      const calendars = this.querySelector('.calendars');
      const dateGrids = this.querySelectorAll('ind-date-grid');
      let calendarDisplayDate, hoverCursor;

      // Populate month names in the select list
      for (let i = 0; i < 12; i++) {
        const date = new Date();
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

      this.addEventListener('x-attrchange.open', () => {
        if (this.open) {
          show();
        } else {
          close();
        }
      });
      this.addEventListener('x-attrchange.range-start', updateCalendar);
      this.addEventListener('x-attrchange.range-end', updateCalendar);
      this.addEventListener('x-rangechange', updateCalendar);

      dialog.addEventListener('pointerdown', () => {
        // Because Safari does not focus buttons (and other elements) when they
        // are clicked, we need to mark the dialog as having received such clicks
        // and test for it in the close handler.
        dialog.noImmediateClose = true;
        setTimeout(() => {
          // Unset with a delay to allow focusout handler to see this flag.
          // It must still be unset so it doesn't linger on forever. The delay
          // was chosen based on trial and error. In general, you don't want
          // to make it shorter, but you may increase it if some browser/OS
          // combination unsets the flag too quickly.
          delete dialog.noImmediateClose;
        }, 100);
      });

      dialog.addEventListener('focusout', () => {
        // The focusout event is triggered on the dialog or somewhere in it.
        // We use requestAnimationFrame to allow the target element to get
        // focused so we know where the focus is going.
        requestAnimationFrame(() => {
          // When a button in the dialog is clicked, `noImmediateClose` is set on
          // the dialog element. We test for the absence of this flag as well as
          // focus escaping from the dialog as two cues to close it.
          if (!dialog.noImmediateClose && !dialog.contains(document.activeElement)) {
            this.open = false;
          }
        });
      });

      // Handle open/close to prep the dialog state
      dialog.addEventListener('open', () => {
        dialog.focus();
      });
      dialog.addEventListener('close', () => {
        calendarDisplayDate = undefined;
        updateCalendar();
      });

      // Handle calendar interaction
      dialog.addEventListener('click', evt => {
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

      // Handle closing/opening the dialog by clicking outside
      indCalendar.addEventListener('keydown', evt => {
        if (evt.code !== 'Escape') {
          return;
        }
        this.open = false;
        this.dispatchEvent(new Event('x-keyclose'));
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

      // Note that this may not work on iOS Safari. We are not currently explicitly
      // targeting this browser, so we'll leave this as is.
      this.addEventListener('x-connect', () => {
        window.addEventListener('click', handleDialogClose);
      });
      this.addEventListener('x-disconnect', () => {
        window.removeEventListener('click', handleDialogClose);
      });

      function handleDialogClose(evt) {
        if (!indCalendar.open) {
          return;
        }
        if (evt.target.closest('dialog') === dialog) {
          return;
        }
        setTimeout(() => {
          indCalendar.open = false;
        });
      }

      function show() {
        if (!dialog) {
          return;
        }
        if (dialog.open) {
          return;
        }
        updateCalendar();
        dialog.show();
        dialog.dispatchEvent(new Event('open'));
      }

      function close() {
        if (!dialog) {
          return;
        }
        if (!dialog.open) {
          return;
        }
        dialog.close();
        indCalendar.dispatchEvent(new Event('close'));
      }

      function getSelectionRange() {
        return new DateRange(indCalendar.rangeStart, indCalendar.rangeEnd);
      }

      function getHoverRange() {
        // A component that wishes to display the preview must set
        // the `selectionPreview` property on the <ind-calendar> element
        // and the value must be a `Selection` object (see
        // `date_selection.js`).
        //
        // When no valid preview can be created an empty `DateRange` is
        // returned.

        if (!indCalendar.selectionPreview) {
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
        console.log(focusableButtons);
        return (
          focusableButtons.find(button => button.dataset.currentMonth === 'true') ||
          focusableButtons[0]
        );
      }
    }
  }
);

customElements.define(
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
      getWeekdayNames(weekInfo, this.locale).forEach(({full, short}, i) => {
        const headerCell = weekdayLabels[i];
        headerCell.setAttribute('aria-label', full);
        headerCell.setAttribute('title', full);
        headerCell.textContent = short;
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
          focusableButton.tabIndex = 0;
          indDateGrid.dispatchEvent(new Event('x-update-grid'));
        });
      }
    }

    static observedAttributes = ['year', 'month', 'range-start', 'range-end'];

    attributeChangedCallback() {
      this.dispatchEvent(new Event('x-attrchange'));
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

function openDialog(indCalendar, input) {
  positioning.position(
    indCalendar.firstElementChild,
    input,
    positioning.dropdownPositionStrategy,
    () => {
      indCalendar.open = true;
    }
  );
}
