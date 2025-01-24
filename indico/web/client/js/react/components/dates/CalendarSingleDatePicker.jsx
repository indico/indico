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

import '../style/dates.scss';

export default function CalendarSingleDatePicker({onChange, date, minDate, maxDate, ...props}) {
  const calendarRef = useRef();

  useNativeEvent(calendarRef, 'change', evt => {
    onChange(evt.detail.date);
  });

  return (
    <ind-inline-date-picker ref={calendarRef} value={date}>
      <DatePickerInlineCalendar minDate={minDate} maxDate={maxDate} {...props}>
        <DatePickerGrid />
      </DatePickerInlineCalendar>
    </ind-inline-date-picker>
  );
}

CalendarSingleDatePicker.propTypes = {
  onChange: PropTypes.func.isRequired,
  date: PropTypes.string,
  minDate: PropTypes.string,
  maxDate: PropTypes.string,
  yearsBefore: PropTypes.number,
  yearsAfter: PropTypes.number,
};

CalendarSingleDatePicker.defaultProps = {
  date: null,
  minDate: null,
  maxDate: null,
};
