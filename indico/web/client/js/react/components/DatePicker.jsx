// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';

import {FinalField, validators as v} from 'indico/react/forms';
import {Param, Translate} from 'indico/react/i18n';
import {formatDate, ISO_FORMAT} from 'indico/utils/date_format';
import {fromISOLocalDate} from 'indico/utils/date_parser';

import 'indico/custom_elements/ind_date_picker';

const INVALID = '__invalid__';

export default function DatePicker({
  onChange,
  value,
  format = moment.localeData().longDateFormat('L'),
  min,
  max,
  ...inputProps
}) {
  function handleDateChange(ev) {
    const {date} = ev.target.closest('ind-date-picker');
    const invalid = !!ev.target.value && !date;
    onChange(invalid ? INVALID : formatDate(ISO_FORMAT, date));
  }

  const formattedValue = formatDate(format, fromISOLocalDate(value));

  return (
    <ind-date-picker>
      <input
        type="text"
        onChange={handleDateChange}
        defaultValue={formattedValue}
        {...inputProps}
        placeholder={format}
      />
      <button type="button" disabled={inputProps.disabled}>
        <Translate as="span">Open a calendar</Translate>
      </button>
      <ind-calendar
        min={fromISOLocalDate(min)?.toDateString()}
        max={fromISOLocalDate(max)?.toDateString()}
      >
        <dialog>
          <div className="controls">
            <button type="button" value="previous-year">
              <Translate as="span">Previous year</Translate>
            </button>
            <button type="button" value="previous-month">
              <Translate as="span">Previous month</Translate>
            </button>

            <div className="month-year">
              <select />
              <input type="number" required />
            </div>

            <button type="button" value="next-month">
              <Translate as="span">Next month</Translate>
            </button>
            <button type="button" value="next-year">
              <Translate as="span">Next year</Translate>
            </button>
          </div>

          <div className="weekdays">
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>
          <div role="listbox" />
        </dialog>
      </ind-calendar>

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
  min: PropTypes.string,
  max: PropTypes.string,
};

DatePicker.defaultProps = {
  value: undefined,
  format: undefined,
  min: undefined,
  max: undefined,
};

/**
 * Like `FinalField` but for a `DatePicker`.
 */
export function FinalDatePicker({name, ...rest}) {
  const validDate = val =>
    val === INVALID ? Translate.string('The entered date is not valid.') : undefined;
  const validators = [validDate];
  if (rest.min) {
    validators.push(val =>
      val < rest.min
        ? Translate.string('The entered date cannot be earlier than {min}.', {
            min: moment(rest.min).format('L'),
          })
        : undefined
    );
  }
  if (rest.max) {
    validators.push(val =>
      val > rest.max
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
    <FinalField name={name} component={DatePicker} {...rest} validate={v.chain(...validators)} />
  );
}

FinalDatePicker.propTypes = {
  name: PropTypes.string.isRequired,
  min: PropTypes.string,
  max: PropTypes.string,
};

FinalDatePicker.defaultProps = {
  min: undefined,
  max: undefined,
};
