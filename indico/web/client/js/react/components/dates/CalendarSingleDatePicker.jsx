// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'react-dates/initialize';
import React from 'react';
import PropTypes from 'prop-types';
import {DayPickerSingleDateController as DayPicker} from 'react-dates';

import 'react-dates/lib/css/_datepicker.css';
import '../style/dates.scss';

export default class CalendarSingleDatePicker extends React.Component {
  static propTypes = {
    disabledDate: PropTypes.func,
  };

  static defaultProps = {
    disabledDate: () => false,
  };

  state = {
    focused: true,
  };

  onFocusChange = ({focused}) => {
    this.setState({focused});
  };

  render() {
    const {focused} = this.state;
    const {disabledDate, ...props} = this.props;
    return (
      <DayPicker
        focused={focused}
        onFocusChange={this.onFocusChange}
        isOutsideRange={disabledDate}
        hideKeyboardShortcutsPanel
        {...props}
      />
    );
  }
}
