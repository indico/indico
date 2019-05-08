// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'react-dates/initialize';
import PropTypes from 'prop-types';
import React from 'react';
import {SingleDatePicker as ReactDatesSinglePicker} from 'react-dates';

import 'react-dates/lib/css/_datepicker.css';
import './style/dates.scss';


export default class SingleDatePicker extends React.Component {
    static propTypes = {
        disabledDate: PropTypes.func,
    };

    static defaultProps = {
        disabledDate: null,
    };

    state = {
        focused: false,
    };

    onFocusChange = ({focused}) => {
        this.setState({focused});
    };

    render() {
        const {focused} = this.state;
        const {disabledDate} = this.props;
        const filteredProps = Object.entries(this.props).filter(([name]) => {
            return !['name', 'value', 'onBlur', 'onChange', 'onFocus', 'label', 'disabledDate'].includes(name);
        }).reduce((acc, curr) => {
            const [key, value] = curr;
            return {...acc, [key]: value};
        }, {});

        if (disabledDate) {
            filteredProps.isOutsideRange = disabledDate;
        }

        return (
            <ReactDatesSinglePicker focused={focused}
                                    onFocusChange={this.onFocusChange}
                                    showDefaultInputIcon
                                    inputIconPosition="after"
                                    hideKeyboardShortcutsPanel
                                    numberOfMonths={1}
                                    {...filteredProps} />
        );
    }
}
