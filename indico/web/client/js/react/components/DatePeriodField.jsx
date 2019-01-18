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
import {START_DATE, END_DATE} from 'react-dates/constants';
import {DateRangePicker} from 'indico/react/components';
import {serializeDate} from 'indico/utils/date';

import './DatePeriodField.module.scss';


export default class DatePeriodField extends React.Component {
    static propTypes = {
        disabledDate: PropTypes.func,
        onChange: PropTypes.func.isRequired,
        disabled: PropTypes.bool,
        disabledDateFields: PropTypes.oneOf([START_DATE, END_DATE]),
        value: PropTypes.shape({
            startDate: PropTypes.string,
            endDate: PropTypes.string,
        }),
        minimumDays: PropTypes.number,
    };

    static defaultProps = {
        disabledDate: null,
        disabled: false,
        disabledDateFields: null,
        value: null,
        minimumDays: 1,
    };

    shouldComponentUpdate(nextProps, nextState) {
        const {disabled: prevDisabled, value: prevValue} = this.props;
        const {disabled, value} = nextProps;
        return nextState !== this.state || disabled !== prevDisabled || !_.isEqual(prevValue, value);
    }

    getMomentValue(type) {
        const {value} = this.props;
        if (!value || !value[type]) {
            return null;
        }
        return moment(value[type], 'YYYY-MM-DD');
    }

    notifyChange = ({startDate, endDate}) => {
        const {onChange} = this.props;
        onChange({
            startDate: serializeDate(startDate),
            endDate: serializeDate(endDate),
        });
    };

    render() {
        const {disabled, disabledDateFields, minimumDays, disabledDate} = this.props;
        const props = {};

        if (disabledDate) {
            props.isOutsideRange = disabledDate;
        }

        return (
            <div styleName="date-period-field">
                <DateRangePicker {...props}
                                 startDate={this.getMomentValue('startDate')}
                                 endDate={this.getMomentValue('endDate')}
                                 onDatesChange={this.notifyChange}
                                 disabled={disabled || disabledDateFields}
                                 inputIconPosition="before"
                                 minimumNights={minimumDays - 1}
                                 block />
            </div>
        );
    }
}
