// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {formatDate} from 'indico/utils/date_format';
import {createDateParser} from 'indico/utils/date_parser';

import './ind_date_picker.scss';

const DEFAULT_LOCALE = document.documentElement.dataset.canonicalLocale;
const CALENDAR_CELL_COUNT = 42; // 6 rows, 7 days each

customElements.define(
  'ind-date-picker',
  class extends HTMLElement {
    // Last value of the internal id used in the widgets
    static lastId = 0;

    get value() {
      return this.querySelector('input').value;
    }

    get start() {
      return this.getAttribute('start');
    }

    get end() {
      return this.getAttribute('end');
    }

    connectedCallback() {
      const id = `date-picker-${this.constructor.lastId++}`;
      const input = this.querySelector('input');
      const startInput = document.getElementById(this.start);
      const endInput = document.getElementById(this.end);
      const openCalendarButton = this.querySelector('button');
      const formatDescription = this.querySelector('[data-format]');
      const indCalendar = this.querySelector('ind-calendar');

      const dateFormat = formatDescription.textContent
        .split(':')[1]
        .trim()
        .toLowerCase();
      const parseDate = createDateParser(dateFormat);

      indCalendar.format = dateFormat;
      indCalendar.value = toDateString(parseDate(this.value));
      formatDescription.id = `${id}-format`;
      input.setAttribute('aria-describedby', formatDescription.id);
      openCalendarButton.setAttribute('aria-haspopup', 'dialog');
      openCalendarButton.setAttribute('aria-controls', true);

      // This property is defined here rather than in the class because it
      // relies on the parseDate() function created in this scope.
      Object.defineProperty(this, 'date', {
        get: () => parseDate(input.value),
      });

      openCalendarButton.addEventListener('click', () => {
        openCalendarButton.disabled = true;
        requestAnimationFrame(openDialog);
      });
      indCalendar.addEventListener('close', () => {
        openCalendarButton.disabled = false;
      });
      indCalendar.addEventListener('x-keyclose', () => {
        openCalendarButton.disabled = false;
        openCalendarButton.focus();
      });
      indCalendar.addEventListener('x-select', () => {
        setNativeInputValue(input, formatDate(dateFormat, new Date(indCalendar.value)));
        input.select();
        input.focus();
        input.dispatchEvent(new Event('input', {bubbles: true}));
      });
      input.addEventListener('keydown', evt => {
        if (evt.code === 'ArrowDown' && evt.altKey) {
          openDialog();
        }
      });
      input.addEventListener('input', () => {
        indCalendar.value = toDateString(parseDate(this.value));
      });
      startInput?.addEventListener('input', () => {
        indCalendar.rangeStart = toDateString(parseDate(startInput.value));
      });
      endInput?.addEventListener('input', () => {
        indCalendar.rangeEnd = toDateString(parseDate(endInput.value));
      });

      function openDialog() {
        indCalendar.toggleAttribute('data-position-check');
        requestAnimationFrame(() => {
          const inputRect = input.getBoundingClientRect();
          const dialogRect = indCalendar.firstElementChild.getBoundingClientRect();
          const dialogBottom = inputRect.bottom + dialogRect.height;
          const dialogWillFitBelow = dialogBottom < window.innerHeight;
          indCalendar.style.setProperty('--dialog-bottom', dialogWillFitBelow ? 'auto' : '100%');
          indCalendar.toggleAttribute('data-position-check');
          indCalendar.open = true;
        });
      }
    }

    disconnectedCallback() {
      this.cleanup();
    }
  }
);

customElements.define(
  'ind-calendar',
  class extends HTMLElement {
    static lastId = 0;

    constructor() {
      super();
      this.calendarId = this.constructor.lastId++;
      this.weekInfo = getWeekInfoForLocale(this.locale);
    }

    get open() {
      return this.hasAttribute('open');
    }

    set open(isOpen) {
      this.toggleAttribute('open', isOpen);
    }

    get locale() {
      return this.getAttribute('lang') || DEFAULT_LOCALE;
    }

    get value() {
      return this.getAttribute('value');
    }

    set value(value) {
      this.setAttribute('value', value || '');
    }

    get rangeStart() {
      return this.getAttribute('range-start');
    }

    set rangeStart(value) {
      this.setAttribute('range-start', value || '');
    }

    get rangeEnd() {
      return this.getAttribute('range-end');
    }

    set rangeEnd(value) {
      this.setAttribute('range-end', value || '');
    }

    connectedCallback() {
      const indCalendar = this;
      const dialog = this.firstElementChild;
      const monthYearGroup = this.querySelector('.month-year');
      const editMonthSelect = monthYearGroup.querySelector('select');
      const editYearInput = monthYearGroup.querySelector('input');
      const weekdaysGroup = dialog.querySelector('.weekdays');
      const listbox = dialog.querySelector('[role=listbox]');
      let calendarDisplayDate;

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

      // Populate weekday names in the calendar header
      getWeekdayNames(this.weekInfo).forEach(({full, short}, i) => {
        const headerCell = weekdaysGroup.children[i];
        headerCell.setAttribute('aria-label', full);
        headerCell.textContent = short;
        headerCell.id = `calendar-${this.calendarId}-wkd-${i + 1}`;
      });

      // Populate calendar with blank buttons
      for (let i = 0; i < CALENDAR_CELL_COUNT; i++) {
        const calendarButton = document.createElement('button');
        calendarButton.setAttribute('role', 'option');
        calendarButton.setAttribute('aria-describedby', weekdaysGroup.children[i % 6].id);
        calendarButton.tabIndex = -1;
        calendarButton.type = 'button';
        listbox.append(calendarButton);
      }

      this.addEventListener('attrchange.open', () => {
        if (this.open) {
          show();
        } else {
          close();
        }
      });
      this.addEventListener('attrchange.value', updateCalendar);

      dialog.addEventListener('focusout', () => {
        // The focusout event is triggered on the dialog or somewhere in it.
        // We use requestAnimationFrame to allow the target element to get
        // focused so we know where the focus is going.
        requestAnimationFrame(() => {
          // If the focus has moved to an element outside the dialog, we close
          if (dialog.contains(document.activeElement)) {
            return;
          }
          this.open = false;
        });
      });

      // Handle open/close to prep the dialog state
      dialog.addEventListener('open', () => {
        calendarDisplayDate = toOptionalDate(this.value) || getToday();
        const focusTarget = dialog.querySelector('[aria-selected=true]') || dialog;
        focusTarget.focus();
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
            // Date selection
            this.open = false;
            this.value = button.value;
            this.dispatchEvent(new Event('x-select'));
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
      listbox.addEventListener('keydown', evt => {
        const currentDate = listbox.querySelector(':focus');
        const currentDateIndex = Array.prototype.indexOf.call(listbox.children, currentDate);
        switch (evt.code) {
          case 'ArrowRight': {
            evt.preventDefault();
            let nextDate = currentDate?.nextElementSibling;
            if (!nextDate) {
              // We've reached the end. Flip to next month and start from the beginning.
              calendarDisplayDate.setMonth(calendarDisplayDate.getMonth() + 1);
              updateCalendar();
              nextDate = listbox.firstElementChild;
            }
            focusCalendarButton(nextDate);
            break;
          }
          case 'ArrowLeft': {
            evt.preventDefault();
            let previousDate = currentDate?.previousElementSibling;
            if (!previousDate) {
              // We've reached the end. Flip to previous month and start from the end.
              calendarDisplayDate.setMonth(calendarDisplayDate.getMonth() - 1);
              updateCalendar();
              previousDate = listbox.lastElementChild;
            }
            focusCalendarButton(previousDate);
            break;
          }
          case 'ArrowUp': {
            evt.preventDefault();
            let nextIndex = currentDateIndex - 7;
            if (nextIndex < 1) {
              // We've reached the end. Flip to previous month and start from last row.
              nextIndex = listbox.children.length - 7 + currentDateIndex;
              calendarDisplayDate.setMonth(calendarDisplayDate.getMonth() - 1);
              updateCalendar();
            }
            focusCalendarButton(listbox.children[nextIndex] || listbox.lastElementChild);
            break;
          }
          case 'ArrowDown': {
            evt.preventDefault();
            let nextIndex = currentDateIndex + 7;
            if (nextIndex > listbox.children.length - 1) {
              // We've reached the end. Flip to next month and start from the first row.
              nextIndex = currentDateIndex % 7;
              calendarDisplayDate.setMonth(calendarDisplayDate.getMonth() + 1);
              updateCalendar();
            }
            focusCalendarButton(listbox.children[nextIndex] || listbox.firstElementChild);
            break;
          }
        }
      });

      // Handle closing/opening the dialog by clicking outside
      this.addEventListener('keydown', evt => {
        if (evt.code !== 'Escape') {
          return;
        }
        this.open = false;
        this.dispatchEvent(new Event('x-keyclose'));
      });

      // Note that this may not work on iOS Safari. We are not currently explicitly
      // targeting this browser, so we'll leave this as is.
      window.addEventListener('click', handleDialogClose);
      this.cleanup = function() {
        window.removeEventListener('click', handleDialogClose);
      };

      function handleDialogClose(ev) {
        if (!indCalendar.open) {
          return;
        }
        if (ev.target.closest('dialog') === dialog) {
          return;
        }
        setTimeout(function() {
          indCalendar.open = false;
        });
      }

      function focusCalendarButton(calendarButton) {
        const currentlyFocusable = listbox.querySelector('[tabindex="0"]');
        if (currentlyFocusable) {
          currentlyFocusable.tabIndex = -1;
        }
        calendarButton.tabIndex = 0;
        calendarButton.focus();
      }

      function show() {
        if (!dialog) {
          return;
        }
        if (dialog.open) {
          return;
        }
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

      function updateCalendar() {
        const selectedDate = toOptionalDate(indCalendar.value);
        const firstDayOfMonth = new Date(calendarDisplayDate || selectedDate || getToday());
        firstDayOfMonth.setDate(1);
        const firstDayOfCalendar = getFirstDayOfWeek(indCalendar.weekInfo, firstDayOfMonth);

        // Populate the year/month controls

        monthYearGroup.querySelector('select').value = firstDayOfMonth.getMonth();
        editYearInput.value = firstDayOfMonth.getFullYear();

        // Populate the calendar cells

        const month = firstDayOfMonth.getMonth();
        // Note that getDay() returns Sunday as 0, but we need 7 because of the weekInfo API

        const rangeStart = toOptionalDate(indCalendar.rangeStart);
        const rangeEnd = toOptionalDate(indCalendar.rangeEnd);
        const markStart = rangeStart || (rangeEnd && selectedDate);
        const markEnd = rangeEnd || (rangeStart && selectedDate);

        for (let i = 0; i < CALENDAR_CELL_COUNT; i++) {
          const date = new Date(firstDayOfCalendar);
          date.setDate(date.getDate() + i);
          const calendarButton = listbox.querySelector(`button:nth-of-type(${i + 1})`);
          calendarButton.textContent = date.getDate();
          calendarButton.dataset.currentMonth = date.getMonth() === month;
          calendarButton.setAttribute(
            'aria-label',
            date.toLocaleDateString(indCalendar.locale, {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })
          );
          calendarButton.toggleAttribute(
            'data-weekend',
            indCalendar.weekInfo.weekend.includes(date.getDay() + 1)
          );
          calendarButton.tabIndex = -1; // reset tabIndex
          calendarButton.value = toDateString(date);

          // Mark range
          calendarButton.disabled = date < rangeStart || date > rangeEnd;
          calendarButton.toggleAttribute('data-range-start', sameDate(date, markStart));
          calendarButton.toggleAttribute('data-range-end', sameDate(date, markEnd));
          calendarButton.toggleAttribute('data-range', date < markEnd && date > markStart);

          // Mark selected
          if (calendarButton.value === indCalendar.value) {
            calendarButton.setAttribute('aria-selected', true);
          } else {
            calendarButton.removeAttribute('aria-selected');
          }
        }

        const focusableButton =
          listbox.querySelector('[aria-selected]') || listbox.firstElementChild;
        focusableButton.tabIndex = 0;
      }
    }

    disconnectedCallback() {
      this.cleanup();
    }

    static observedAttributes = ['open', 'value', 'range-start', 'range-end'];

    attributeChangedCallback(name) {
      switch (name) {
        case 'open':
          this.dispatchEvent(new Event('attrchange.open'));
          break;
        case 'value':
        case 'range-start':
        case 'range-end':
          this.dispatchEvent(new Event('attrchange.value'));
          break;
      }
    }
  }
);

// React hacks

function setNativeInputValue(input, value) {
  // React adds its own setter to the input and messes with the native event mechanism.
  // In order for the value to be set in a standard way, we need to resort to this hack.
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, value);
}

// Date functions

function getToday() {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return now;
}

function sameDate(a, b) {
  return a?.getTime() === b?.getTime();
}

function toDateString(date) {
  // We do not use ISO date format because it will be interpreted as UTC
  return date?.toDateString();
}

function toOptionalDate(dateString) {
  const date = new Date(dateString);
  if (!date.getTime()) {
    return;
  }
  date.setHours(0, 0, 0, 0);
  return date;
}

// Localization

function getWeekInfoForLocale(locale) {
  let weekInfo = new Intl.Locale(locale).weekInfo;
  weekInfo ??= {firstDay: 7, weekend: [6, 7]}; /* Firefox 😭 */
  weekInfo.weekDays = [];
  for (let i = weekInfo.firstDay, end = i + 7; i < end; i++) {
    weekInfo.weekDays.push(i % 7 || 7);
  }
  return weekInfo;
}

function getFirstDayOfWeek(weekInfo, date) {
  const offset = weekInfo.weekDays.indexOf(date.getDay() || 7);
  const firstDayOfWeek = new Date(date);
  firstDayOfWeek.setDate(firstDayOfWeek.getDate() - offset);
  return firstDayOfWeek;
}

function getWeekdayNames(weekInfo, locale) {
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
