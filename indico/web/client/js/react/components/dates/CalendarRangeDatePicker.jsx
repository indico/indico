// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useRef} from 'react';

import {DatePickerGrid, DatePickerInlineCalendar} from 'indico/react/components/DatePickerCalendar';
import {useNativeEvent} from 'indico/react/hooks';
import {formatDate, ISO_FORMAT} from 'indico/utils/date_format';

import '../style/dates.scss';

export default function CalendarRangeDatePicker({
  onChange,
  startDate,
  endDate,
  minDate,
  maxDate,
  ...props
}) {
  const calendarRef = useRef();

  useNativeEvent(calendarRef, 'change', evt => {
    const {left, right} = evt.detail;
    onChange({
      startDate: formatDate(ISO_FORMAT, left),
      endDate: formatDate(ISO_FORMAT, right),
    });
  });

  return (
    <ind-inline-date-range-picker ref={calendarRef} range-start={startDate} range-end={endDate}>
      <DatePickerInlineCalendar
        minDate={minDate}
        maxDate={maxDate}
        rangeStart={startDate}
        rangeEnd={endDate}
        {...props}
      >
        <div className="calendars">
          <DatePickerGrid includeMonthHeader />
          <DatePickerGrid includeMonthHeader />
        </div>
      </DatePickerInlineCalendar>
    </ind-inline-date-range-picker>
  );
}

CalendarRangeDatePicker.propTypes = {
  onChange: PropTypes.func.isRequired,
  startDate: PropTypes.string,
  endDate: PropTypes.string,
  minDate: PropTypes.string,
  maxDate: PropTypes.string,
  yearsBefore: PropTypes.number,
  yearsAfter: PropTypes.number,
};

CalendarRangeDatePicker.defaultProps = {
  startDate: null,
  endDate: null,
  minDate: null,
  maxDate: null,
};
