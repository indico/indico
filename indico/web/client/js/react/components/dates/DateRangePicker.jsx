// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'react-dates/initialize';
import {useState} from 'react';
import {DateRangePicker as ReactDatesRangePicker} from 'react-dates';
import {responsiveReactDates} from './util';

import 'react-dates/lib/css/_datepicker.css';
import '../style/dates.scss';

const DateRangePicker = props => {
  const [focusedInput, setFocusedInput] = useState(null);
  return responsiveReactDates(ReactDatesRangePicker, {
    ...props,
    startDateId: 'start_date',
    endDateId: 'end_date',
    inputIconPosition: 'after',
    showDefaultInputIcon: true,
    hideKeyboardShortcutsPanel: true,
    focusedInput,
    onFocusChange: setFocusedInput,
  });
};

export default DateRangePicker;
