// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';

import DatePickerCalendar from 'indico/react/components/DatePickerCalendar';
import {FinalField, validators as v} from 'indico/react/forms';
import {Param, Translate} from 'indico/react/i18n';
import {DateRange} from 'indico/utils/date';
import {formatDate, ISO_FORMAT} from 'indico/utils/date_format';
import {fromISOLocalDate} from 'indico/utils/date_parser';

import 'indico/custom_elements/ind_date_picker';

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
  onChange,
}) {
  format ??= moment.localeData().longDateFormat('L');

  if (min) {
    rangeStartMin = rangeStartMax = min;
  }

  if (max) {
    rangeEndMin = rangeEndMax = max;
  }

  function handleChange(ev) {
    const picker = ev.currentTarget;
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

  return (
    <ind-date-range-picker
      range-start={fromISOLocalDate(value.startDate)?.toDateString() || ''}
      range-end={fromISOLocalDate(value.endDate)?.toDateString() || ''}
      range-start-min={rangeStartMin}
      range-start-max={rangeStartMax}
      range-end-min={rangeEndMin}
      range-end-max={rangeEndMax}
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
            disabled={disabled}
          />
        </label>
        <button type="button" data-calendar-trigger="left">
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
            disabled={disabled}
          />
        </label>
        <button type="button" data-calendar-trigger="right">
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
          <DatePickerCalendar.Grid includeMonthHeader />
          <DatePickerCalendar.Grid includeMonthHeader />
        </div>
      </DatePickerCalendar>
    </ind-date-range-picker>
  );
}

DateRangePicker.propTypes = {
  format: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  readOnly: PropTypes.bool,
  disabled: PropTypes.bool,
  value: PropTypes.object,
  label: PropTypes.string,
  rangeStartLabel: PropTypes.string.isRequired,
  rangeEndLabel: PropTypes.string.isRequired,
  rangeStartMin: PropTypes.string,
  rangeStartMax: PropTypes.string,
  rangeEndMin: PropTypes.string,
  rangeEndMax: PropTypes.string,
  min: PropTypes.string,
  max: PropTypes.string,
};

DateRangePicker.defaultProps = {
  format: undefined,
  value: {startDate: '', endDate: ''},
  readOnly: false,
  disabled: false,
  label: Translate.string('Select a date range'),
  rangeStartMin: '',
  rangeStartMax: '',
  rangeEndMin: '',
  rangeEndMax: '',
  min: '',
  max: '',
};

function validDate(key, message) {
  return function(values) {
    const value = values[key];
    if (value !== INVALID) {
      return;
    }
    return message;
  };
}

function validDateRange(min, max, key, message) {
  const range = new DateRange(min, max);
  return function(values) {
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
      Translate.string('Please enter the start date using the specified format')
    ),
    validDate('endDate', Translate.string('Please enter the end date using the specified format')),
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
      validate={v.chain(...validators)}
    />
  );
}

FinalDateRangePicker.propTypes = {
  name: PropTypes.string.isRequired,
  format: PropTypes.string,
  rangeStartMin: PropTypes.string,
  rangeStartMax: PropTypes.string,
  rangeEndMin: PropTypes.string,
  rangeEndMax: PropTypes.string,
};

FinalDateRangePicker.defaultProps = {
  format: undefined,
  rangeStartMin: '',
  rangeStartMax: '',
  rangeEndMin: '',
  rangeEndMax: '',
};
