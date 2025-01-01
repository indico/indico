// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'react-dates/initialize';
import PropTypes from 'prop-types';
import React from 'react';
import {DayPickerRangeController as RangePicker} from 'react-dates';

import 'react-dates/lib/css/_datepicker.css';
import '../style/dates.scss';
import {responsiveReactDates} from './util';

export default class CalendarRangeDatePicker extends React.Component {
  static propTypes = {
    disabledDate: PropTypes.func,
  };

  static defaultProps = {
    disabledDate: () => false,
  };

  state = {
    focusedInput: 'startDate',
  };

  onFocusChange = focusedInput => {
    this.setState({focusedInput: focusedInput || 'startDate'});
  };

  render() {
    const {focusedInput} = this.state;
    const {disabledDate, ...props} = this.props;
    return responsiveReactDates(RangePicker, {
      ...props,
      focusedInput,
      onFocusChange: this.onFocusChange,
      isOutsideRange: disabledDate,
      hideKeyboardShortcutsPanel: true,
      numberOfMonths: 2,
    });
  }
}
