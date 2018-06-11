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
import 'rc-calendar/assets/index.css';
import {toMoment} from '../../util';

import FilterFormComponent from './FilterFormComponent';

import './DateForm.module.scss';


const _serializeDate = dt => (dt ? dt.format('YYYY-MM-DD') : null);

export default class DateForm extends FilterFormComponent {
    static propTypes = {
        startDate: propTypes.string,
        endDate: propTypes.string,
        isRange: propTypes.bool.isRequired,
        handleClose: propTypes.func.isRequired,
        ...FilterFormComponent.propTypes
    };

    static defaultProps = {
        startDate: null,
        endDate: null
    };

    static getDerivedStateFromProps({startDate, endDate}, prevState) {
        // if there is no internal state, get the values from props
        return {
            ...prevState,
            startDate: prevState.startDate || toMoment(startDate),
            endDate: prevState.endDate || toMoment(endDate)
        };
    }

    setDates(startDate, endDate) {
        // return a promise that awaits the state update
        return new Promise((resolve) => {
            const {setParentField} = this.props;
            // send serialized versions to parent/redux
            setParentField('startDate', _serializeDate(startDate));
            setParentField('endDate', _serializeDate(endDate));
            this.setState({
                startDate,
                endDate
            }, () => {
                resolve();
            });
        });
    }

    disabledDate(current) {
        return current.isBefore(moment(), 'day');
    }

    render() {
        const {isRange, handleClose} = this.props;
        const {startDate, endDate} = this.state;
        const props = {
            getPopupContainer: trigger => trigger.parentNode
        };
        return (
            <div styleName="date-form">
                {isRange ? (
                    <RangeCalendar selectedValue={[startDate, endDate]}
                                   onSelect={async ([start, end]) => {
                                       await this.setDates(start, end);
                                       handleClose();
                                   }}
                                   disabledDate={this.disabledDate}
                                   {...props} />
                ) : (
                    <RcCalendar selectedValue={startDate}
                                onSelect={async (date) => {
                                    await this.setDates(date, null);
                                    handleClose();
                                }}
                                disabledDate={this.disabledDate}
                                {...props} />
                ) }
            </div>
        );
    }
}
