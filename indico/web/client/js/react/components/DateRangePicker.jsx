// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';

import {DatePickerCalendar, DatePickerGrid} from 'indico/react/components/DatePickerCalendar';
import {FinalField, validators as v} from 'indico/react/forms';
import {Param, Translate} from 'indico/react/i18n';
import {DateRange} from 'indico/utils/date';
import {formatDate, ISO_FORMAT} from 'indico/utils/date_format';
import {fromISOLocalDate} from 'indico/utils/date_parser';

const INVALID = '__invalid__';

export default function DateRangePicker({
  value,
  label,
  format,
  rangeStartLabel,
  rangeEndLabel,
  rangeStartMin,
  rangeStartMax,
  rangeEndMin,
  rangeEndMax,
  min,
  max,
  readOnly,
  disabled,
  startDisabled,
  endDisabled,
  onChange,
  onFocus,
  onBlur,
  filter,
}) {
  format ??= moment.localeData().longDateFormat('L');

  if (startDisabled && !value?.startDate) {
    console.warn('startDisabled is ignored because value.startDate is not specified');
  }
  if (endDisabled && !value?.endDate) {
    console.warn('endDisabled is ignored because value.endDate is not specified');
  }
  const startLocked = disabled || (value?.startDate && startDisabled);
  const endLocked = disabled || (value?.endDate && endDisabled);

  if (min) {
    rangeStartMin = rangeEndMin = min;
  }

  if (max) {
    rangeEndMax = rangeEndMax = max;
  }

  function handleChange(evt) {
    const picker = evt.currentTarget;
    const [start, end] = picker.dateRange;
    const rangeStartInput = picker.querySelector('[data-range-start]');
    const rangeEndInput = picker.querySelector('[data-range-end]');

    const startInvalid = rangeStartInput.value && !start;
    const endInvalid = rangeEndInput.value && !end;

    onChange({
      // ISO local dates
      startDate: startInvalid ? INVALID : formatDate(ISO_FORMAT, start) || null,
      endDate: endInvalid ? INVALID : formatDate(ISO_FORMAT, end) || null,
    });
  }

  const markTouched = () => {
    if (onFocus && onBlur) {
      onFocus();
      onBlur();
    }
  };

  return (
    <ind-date-range-picker
      range-start={fromISOLocalDate(value?.startDate)?.toDateString() || ''}
      range-end={fromISOLocalDate(value?.endDate)?.toDateString() || ''}
      range-start-min={rangeStartMin}
      range-start-max={rangeStartMax}
      range-end-min={rangeEndMin}
      range-end-max={rangeEndMax}
      format={format}
      onChange={handleChange}
    >
      <fieldset>
        <legend>{label}</legend>
        <label>
          <span>{rangeStartLabel}:</span>
          <input
            type="text"
            data-range-start
            placeholder={format}
            readOnly={readOnly}
            disabled={startLocked || disabled}
            onFocus={onFocus}
            onBlur={onBlur}
          />
        </label>
        <button
          type="button"
          data-calendar-trigger="left"
          disabled={startLocked || readOnly || disabled}
          onClick={markTouched}
        >
          <Translate as="span">Open a calendar</Translate>
        </button>
        <span className="arrow" />
        <label>
          <span>{rangeEndLabel}:</span>
          <input
            type="text"
            data-range-end
            placeholder={format}
            readOnly={readOnly}
            disabled={endLocked || disabled}
            onFocus={onFocus}
            onBlur={onBlur}
          />
        </label>
        <button
          type="button"
          data-calendar-trigger="right"
          disabled={endLocked || readOnly || disabled}
          onClick={markTouched}
        >
          <Translate as="span">Open a calendar</Translate>
        </button>

        <span className="date-format" data-format>
          <Translate>
            Date format: <Param name="format" value={format} />
          </Translate>
        </span>
      </fieldset>

      <DatePickerCalendar>
        <div className="calendars">
          <DatePickerGrid filter={filter} includeMonthHeader />
          <DatePickerGrid filter={filter} includeMonthHeader />
        </div>
      </DatePickerCalendar>
    </ind-date-range-picker>
  );
}

DateRangePicker.propTypes = {
  format: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func,
  onBlur: PropTypes.func,
  readOnly: PropTypes.bool,
  disabled: PropTypes.bool,
  startDisabled: PropTypes.bool,
  endDisabled: PropTypes.bool,
  value: PropTypes.shape({
    startDate: PropTypes.string,
    endDate: PropTypes.string,
  }),
  label: PropTypes.string,
  rangeStartLabel: PropTypes.string,
  rangeEndLabel: PropTypes.string,
  rangeStartMin: PropTypes.string,
  rangeStartMax: PropTypes.string,
  rangeEndMin: PropTypes.string,
  rangeEndMax: PropTypes.string,
  min: PropTypes.string,
  max: PropTypes.string,
  filter: PropTypes.func,
};

DateRangePicker.defaultProps = {
  format: undefined,
  value: {startDate: '', endDate: ''},
  readOnly: false,
  disabled: false,
  startDisabled: false,
  endDisabled: false,
  label: Translate.string('Select a date range'),
  rangeStartLabel: Translate.string('Start'),
  rangeEndLabel: Translate.string('End'),
  rangeStartMin: '',
  rangeStartMax: '',
  rangeEndMin: '',
  rangeEndMax: '',
  min: '',
  max: '',
  filter: undefined,
};

function validDate(key, required, invalidMessage, missingMessage) {
  return values => {
    const value = values[key];
    if (!value && required) {
      return missingMessage;
    }
    if (value !== INVALID) {
      return;
    }
    return invalidMessage;
  };
}

function validDateRange(min, max, key, message) {
  const range = new DateRange(min, max);
  return values => {
    const value = values[key];
    if (!value || value === INVALID) {
      return;
    }
    if (range.includes(value)) {
      return;
    }
    return message;
  };
}

export function FinalDateRangePicker({name, ...props}) {
  const dateFormat = props.format || moment.localeData().longDateFormat('L');

  const validators = [
    validDate(
      'startDate',
      props.required,
      Translate.string('Please enter the start date using the specified format'),
      Translate.string('Please provide the start date')
    ),
    validDate(
      'endDate',
      props.required,
      Translate.string('Please enter the end date using the specified format'),
      Translate.string('Please provide the end date')
    ),
  ];

  if (props.rangeStartMin && props.rangeStartMax) {
    validators.push(
      validDateRange(
        props.rangeStartMin,
        props.rangeStartMax,
        'startDate',
        Translate.string('Please make sure the start date is between {start} and {end}', {
          start: formatDate(dateFormat, fromISOLocalDate(props.rangeStartMin)),
          end: formatDate(dateFormat, fromISOLocalDate(props.rangeStartMax)),
        })
      )
    );
  }

  if (props.rangeEndMin && props.rangeEndMax) {
    validators.push(
      validDateRange(
        props.rangeEndMin,
        props.rangeEndMax,
        'endDate',
        Translate.string('Please make sure the end date is between {start} and {end}', {
          start: formatDate(dateFormat, fromISOLocalDate(props.rangeEndMin)),
          end: formatDate(dateFormat, fromISOLocalDate(props.rangeEndMax)),
        })
      )
    );
  }

  return (
    <FinalField
      name={name}
      {...props}
      component={DateRangePicker}
      validate={val => {
        const res = v.chain(...validators)(val);
        return res;
      }}
    />
  );
}

FinalDateRangePicker.propTypes = {
  name: PropTypes.string.isRequired,
  format: PropTypes.string,
  required: PropTypes.bool,
  rangeStartMin: PropTypes.string,
  rangeStartMax: PropTypes.string,
  rangeEndMin: PropTypes.string,
  rangeEndMax: PropTypes.string,
  startDisabled: PropTypes.bool,
  endDisabled: PropTypes.bool,
};

FinalDateRangePicker.defaultProps = {
  format: undefined,
  required: false,
  rangeStartMin: '',
  rangeStartMax: '',
  rangeEndMin: '',
  rangeEndMax: '',
  startDisabled: false,
  endDisabled: false,
};
