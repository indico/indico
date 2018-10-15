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

import _ from 'lodash';
import moment from 'moment';
import React from 'react';
import PropTypes from 'prop-types';
import RangeCalendar from 'rc-calendar/lib/RangeCalendar';
import {serializeDate} from 'indico/utils/date';

import './DatePeriodField.module.scss';


export default class DatePeriodField extends React.Component {
    static propTypes = {
        onChange: PropTypes.func.isRequired,
        disabled: PropTypes.bool,
        disabledDate: PropTypes.func,
        value: PropTypes.shape({
            startDate: PropTypes.string,
            endDate: PropTypes.string,
        }),
        format: PropTypes.string,
    };

    static defaultProps = {
        disabled: false,
        disabledDate: null,
        value: null,
        format: 'L',
    };

    shouldComponentUpdate(nextProps, nextState) {
        const {disabled: prevDisabled, value: prevValue} = this.props;
        const {disabled, value} = nextProps;
        return nextState !== this.state || disabled !== prevDisabled || !_.isEqual(prevValue, value);
    }

    get momentValue() {
        const {value} = this.props;
        if (!value) {
            return null;
        }
        return [moment(value.startDate, 'YYYY-MM-DD'), moment(value.endDate, 'YYYY-MM-DD')];
    }

    notifyChange = (values) => {
        const {onChange} = this.props;
        onChange({
            startDate: serializeDate(values[0]),
            endDate: serializeDate(values[1]),
        });
    };

    render() {
        const {disabledDate, disabled, format} = this.props;
        return (
            <RangeCalendar styleName="date-period-field"
                           className={disabled ? 'disabled' : ''}
                           format={format}
                           onSelect={this.notifyChange}
                           selectedValue={this.momentValue}
                           disabledDate={(date) => (disabledDate ? disabledDate(date) : null)}
                           showToday={!disabled} />
        );
    }
}
