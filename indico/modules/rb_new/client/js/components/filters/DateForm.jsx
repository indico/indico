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

import React from 'react';
import RangeCalendar from 'rc-calendar/lib/RangeCalendar';
import RcCalendar from 'rc-calendar';
import propTypes from 'prop-types';
// Import date-picker style from ant, since range calendar has none
import 'antd/lib/date-picker/style/css';
import {toMoment} from '../../util';


const _serializeDate = dt => (dt ? dt.format('YYYY-MM-DD') : null);

export default class DateForm extends React.Component {
    static propTypes = {
        startDate: propTypes.string,
        endDate: propTypes.string,
        setParentField: propTypes.func.isRequired,
        isRange: propTypes.bool.isRequired
    };

    static defaultProps = {
        startDate: null,
        endDate: null
    };

    static getDerivedStateFromProps({startDate, endDate}, prevState) {
        // if there is no internal state, get the values from props
        return {
            ...prevState,
            startDate: prevState.startDate ? prevState.startDate : toMoment(startDate),
            endDate: prevState.endDate ? prevState.endDate : toMoment(endDate)
        };
    }

    constructor(props) {
        super(props);
        this.state = {};
    }

    resetFields(fields) {
        // version from parent/redux will be serialized
        this.setDates(toMoment(fields.startDate), toMoment(fields.endDate));
    }

    setDates(startDate, endDate) {
        const {setParentField} = this.props;
        // send serialized versions to parent/redux
        setParentField('startDate', _serializeDate(startDate));
        setParentField('endDate', _serializeDate(endDate));
        this.setState({
            startDate,
            endDate
        });
    }

    render() {
        const {isRange} = this.props;
        const {startDate, endDate} = this.state;
        const props = {
            prefixCls: 'ant-calendar',
            getPopupContainer: trigger => trigger.parentNode
        };
        return (
            <div>
                {isRange ? (
                    <RangeCalendar selectedValue={[startDate, endDate]}
                                   onChange={(([start, end]) => {
                                       if (start && end) {
                                           this.setDates(start, end);
                                       }
                                   })}
                                   {...props} />
                ) : (
                    <RcCalendar selectedValue={startDate}
                                onChange={((date) => {
                                    this.setDates(date, null);
                                })}
                                {...props} />
                ) }
            </div>
        );
    }
}
