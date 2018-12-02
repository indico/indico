/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

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
    };f

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
