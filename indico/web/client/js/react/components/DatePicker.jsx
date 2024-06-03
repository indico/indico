// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';

import {Param, Translate} from 'indico/react/i18n';
import {formatDate} from 'indico/utils/date_format';
import {fromISOLocalDate} from 'indico/utils/date_parser';

import 'indico/custom_elements/ind_date_picker';

export default function DatePicker({
  onChange,
  value,
  format = moment.localeData().longDateFormat('L'),
  ...inputProps
}) {
  function handleDateChange(ev) {
    const {date} = ev.target.closest('ind-date-picker');
    // en-CA uses the ISO format date (YYYY-MM-DD) but gives it in local time zone.
    // Do not use toISOString() for this because it may result in incorrect date due
    // to time zone differences.
    onChange(date?.toLocaleDateString('en-CA'));
  }

  const formattedValue = formatDate(format, fromISOLocalDate(value));

  return (
    <ind-date-picker>
      <input
        type="text"
        onChange={handleDateChange}
        defaultValue={formattedValue}
        placeholder={format}
        {...inputProps}
      />
      <button type="button" disabled={inputProps.disabled}>
        <Translate as="span">Open a calendar</Translate>
      </button>
      <ind-calendar>
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
};

DatePicker.defaultProps = {
  value: undefined,
  format: undefined,
};
