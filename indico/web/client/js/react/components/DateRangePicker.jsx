// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'react-dates/initialize';
import React from 'react';
import {DateRangePicker as ReactDatesRangePicker} from 'react-dates';

import 'react-dates/lib/css/_datepicker.css';
import './style/dates.scss';


export default class DateRangePicker extends React.Component {
    state = {
        focusedInput: null,
    };

    onFocusChange = (focusedInput) => {
        this.setState({focusedInput});
    };

    render() {
        const {focusedInput} = this.state;
        return (
            <ReactDatesRangePicker startDateId="start_date"
                                   endDateId="end_date"
                                   focusedInput={focusedInput}
                                   onFocusChange={this.onFocusChange}
                                   showDefaultInputIcon
                                   inputIconPosition="after"
                                   hideKeyboardShortcutsPanel
                                   {...this.props} />
        );
    }
}
