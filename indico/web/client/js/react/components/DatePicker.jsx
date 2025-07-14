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
import {formatDate, ISO_FORMAT} from 'indico/utils/date_format';
import {fromISOLocalDate} from 'indico/utils/date_parser';

export const INVALID = '__invalid__';

export default function DatePicker({
  onChange,
  value,
  format = moment.localeData().longDateFormat('L'),
  invalidValue = INVALID,
  min,
  max,
  filter,
  ...inputProps
}) {
  function handleDateChange(evt) {
    const {date} = evt.target.closest('ind-date-picker');
    const invalid = !!evt.target.value && !date;
    onChange(invalid ? invalidValue : formatDate(ISO_FORMAT, date));
  }

  const formattedValue = formatDate(format, fromISOLocalDate(value));

  return (
    <ind-date-picker
      min={fromISOLocalDate(min)?.toDateString()}
      max={fromISOLocalDate(max)?.toDateString()}
      format={format}
    >
      <input
        type="text"
        onChange={handleDateChange}
        defaultValue={formattedValue}
        {...inputProps}
        placeholder={format}
      />
      <button
        type="button"
        disabled={inputProps.disabled}
        aria-haspopup="dialog"
        data-calendar-trigger
      >
        <Translate as="span">Open a calendar</Translate>
      </button>

      <DatePickerCalendar>
        <DatePickerGrid filter={filter} />
      </DatePickerCalendar>

      <span className="date-format" data-format>
        <Translate>
          Date format: <Param name="format" value={format} />
        </Translate>
      </span>
    </ind-date-picker>
  );
}

DatePicker.propTypes = {
  format: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  value: PropTypes.any,
  invalidValue: PropTypes.any,
  min: PropTypes.string,
  max: PropTypes.string,
  filter: PropTypes.func,
};

DatePicker.defaultProps = {
  value: undefined,
  format: undefined,
  min: undefined,
  max: undefined,
  filter: undefined,
};

/** Like DatePicker, but using a range-like value */
function RangedDatePicker({value, onChange, ...rest}) {
  const handleChange = newDate => {
    onChange({
      startDate: newDate,
      endDate: null,
    });
  };
  return <DatePicker value={value.startDate} onChange={handleChange} {...rest} />;
}

RangedDatePicker.propTypes = {
  value: PropTypes.shape({
    startDate: PropTypes.string.isRequired,
    // endDate: null  -- not supported by propTypes :(
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};

/**
 * Like `FinalField` but for a `DatePicker`.
 */
export function FinalDatePicker({name, asRange, ...rest}) {
  const getRealVal = val => (asRange ? val.startDate : val);
  const validDate = val =>
    getRealVal(val) === INVALID ? Translate.string('The entered date is not valid.') : undefined;
  const validators = [validDate];
  if (rest.min) {
    validators.push(val =>
      getRealVal(val) < rest.min
        ? Translate.string('The entered date cannot be earlier than {min}.', {
            min: moment(rest.min).format('L'),
          })
        : undefined
    );
  }
  if (rest.max) {
    validators.push(val =>
      getRealVal(val) > rest.max
        ? Translate.string('The entered date cannot be later than {max}.', {
            max: moment(rest.max).format('L'),
          })
        : undefined
    );
  }
  if (rest.validate) {
    validators.push(rest.validate);
  }
  return (
    <FinalField
      name={name}
      component={asRange ? RangedDatePicker : DatePicker}
      {...rest}
      validate={v.chain(...validators)}
    />
  );
}

FinalDatePicker.propTypes = {
  name: PropTypes.string.isRequired,
  min: PropTypes.string,
  max: PropTypes.string,
  asRange: PropTypes.bool,
};

FinalDatePicker.defaultProps = {
  min: undefined,
  max: undefined,
  asRange: false,
};
