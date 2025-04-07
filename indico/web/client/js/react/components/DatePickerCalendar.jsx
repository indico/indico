// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useRef, useEffect} from 'react';

import {Translate} from 'indico/react/i18n';
import {OpenDateRange} from 'indico/utils/date';
import {formatDate, ISO_FORMAT} from 'indico/utils/date_format';
import {fromISOLocalDate} from 'indico/utils/date_parser';

const NUM_DAYS_PER_WEEK = 7;
const NUM_CALENDAR_CELLS = 42; // 6 weeks x 7 days

export function DatePickerGrid({includeMonthHeader = false}) {
  return (
    <ind-date-grid data-grid>
      {includeMonthHeader ? <div className="month-label" data-month-label /> : null}
      <div className="weekdays" data-weekday-labels>
        {_.range(NUM_DAYS_PER_WEEK).map(i => (
          <abbr key={i} />
        ))}
      </div>
      <div role="listbox">
        {_.range(NUM_CALENDAR_CELLS).map(i => (
          <button type="button" role="option" key={i} />
        ))}
      </div>
    </ind-date-grid>
  );
}

DatePickerGrid.propTypes = {
  includeMonthHeader: PropTypes.bool,
};

DatePickerGrid.defaultProps = {
  includeMonthHeader: false,
};

export const DatePickerCalendar = React.forwardRef(({inline = false, children, ...props}, ref) => {
  const Wrapper = inline ? 'div' : 'dialog';
  return (
    <ind-calendar ref={ref} {...props}>
      <Wrapper>
        <div className="controls">
          <button type="button" value="previous-year">
            <Translate as="span">Previous year</Translate>
          </button>
          <button type="button" value="previous-month">
            <Translate as="span">Previous month</Translate>
          </button>

          <div className="month-year">
            <select data-internal />
            <input type="number" required data-internal />
          </div>

          <button type="button" value="next-month">
            <Translate as="span">Next month</Translate>
          </button>
          <button type="button" value="next-year">
            <Translate as="span">Next year</Translate>
          </button>
        </div>

        {children}
      </Wrapper>
    </ind-calendar>
  );
});

DatePickerCalendar.displayName = 'DatePickerCalendar';

DatePickerCalendar.propTypes = {
  inline: PropTypes.bool,
  children: PropTypes.node.isRequired,
};

DatePickerCalendar.defaultProps = {
  inline: false,
};

export function DatePickerInlineCalendar({
  onChange,
  children,
  rangeStart,
  rangeEnd,
  minDate,
  maxDate,
}) {
  const calendarRef = useRef();

  useEffect(() => {
    const selectionRange = new OpenDateRange(fromISOLocalDate(minDate), fromISOLocalDate(maxDate));
    calendarRef.current.setAllowableSelectionRange(selectionRange);
  }, [minDate, maxDate]);

  useEffect(() => {
    const abortController = new AbortController();
    calendarRef.current.addEventListener(
      'x-select',
      evt => {
        onChange(formatDate(ISO_FORMAT, new Date(evt.target.value)));
      },
      {signal: abortController.signal}
    );
    return () => abortController.abort();
  }, [onChange]);

  return (
    <DatePickerCalendar
      inline
      ref={calendarRef}
      open
      range-start={fromISOLocalDate(rangeStart)?.toDateString()}
      range-end={fromISOLocalDate(rangeEnd)?.toDateString()}
      onChange={onChange}
    >
      {children}
    </DatePickerCalendar>
  );
}

DatePickerInlineCalendar.propTypes = {
  onChange: PropTypes.func,
  children: PropTypes.node.isRequired,
  rangeStart: PropTypes.string,
  rangeEnd: PropTypes.string,
  minDate: PropTypes.string,
  maxDate: PropTypes.string,
};

DatePickerInlineCalendar.defaultProps = {
  onChange: () => {},
  rangeStart: undefined,
  rangeEnd: undefined,
  minDate: undefined,
  maxDate: undefined,
};
