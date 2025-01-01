// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'react-dates/initialize';
import PropTypes from 'prop-types';
import React from 'react';
import {DayPickerSingleDateController as DayPicker} from 'react-dates';

import {renderMonthElement, responsiveReactDates} from './util';

import 'react-dates/lib/css/_datepicker.css';
import '../style/dates.scss';

export default class CalendarSingleDatePicker extends React.Component {
  static propTypes = {
    disabledDate: PropTypes.func,
    yearsBefore: PropTypes.number,
    yearsAfter: PropTypes.number,
  };

  static defaultProps = {
    disabledDate: () => false,
    yearsBefore: 5,
    yearsAfter: 5,
  };

  state = {
    focused: true,
  };

  onFocusChange = ({focused}) => {
    this.setState({focused});
  };

  render() {
    const {focused} = this.state;
    const {disabledDate, yearsBefore, yearsAfter, ...props} = this.props;
    return responsiveReactDates(DayPicker, {
      ...props,
      focused,
      onFocusChange: this.onFocusChange,
      isOutsideRange: disabledDate,
      hideKeyboardShortcutsPanel: true,
      renderMonthElement: params => renderMonthElement(yearsBefore, yearsAfter, params),
    });
  }
}
