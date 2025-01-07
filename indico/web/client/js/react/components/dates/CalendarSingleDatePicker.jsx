// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'react-dates/initialize';
import PropTypes from 'prop-types';
import React from 'react';

import {DatePickerGrid, DatePickerInlineCalendar} from 'indico/react/components/DatePickerCalendar';

import '../style/dates.scss';

export default function CalendarSingleDatePicker({date, minDate, maxDate, ...props}) {
  return (
    <DatePickerInlineCalendar
      minDate={minDate}
      maxDate={maxDate}
      rangeStart={date}
      rangeEnd={date}
      {...props}
    >
      <DatePickerGrid />
    </DatePickerInlineCalendar>
  );
}

CalendarSingleDatePicker.propTypes = {
  date: PropTypes.object,
  minDate: PropTypes.object,
  maxDate: PropTypes.object,
  yearsBefore: PropTypes.number,
  yearsAfter: PropTypes.number,
};

CalendarSingleDatePicker.defaultProps = {
  date: null,
  minDate: null,
  maxDate: null,
};
