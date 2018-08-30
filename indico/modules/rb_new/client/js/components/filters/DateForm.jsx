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

import moment from 'moment';
import React from 'react';
import RangeCalendar from 'rc-calendar/lib/RangeCalendar';
import RCCalendar from 'rc-calendar';
import PropTypes from 'prop-types';
import 'rc-calendar/assets/index.css';
import {toMoment} from '../../util';

import FilterFormComponent from './FilterFormComponent';

import './DateForm.module.scss';


const _formatDateStr = 'YYYY-MM-DD';
const _serializeDate = date => (date ? date.format(_formatDateStr) : null);

export default class DateForm extends FilterFormComponent {
    static propTypes = {
        startDate: PropTypes.string,
        endDate: PropTypes.string,
        isRange: PropTypes.bool.isRequired,
        handleClose: PropTypes.func.isRequired,
        disabledDate: PropTypes.func,
        ...FilterFormComponent.propTypes
    };

    static defaultProps = {
        startDate: null,
        endDate: null,
        disabledDate: null
    };

    static getDerivedStateFromProps({startDate, endDate}, prevState) {
        // if there is no internal state, get the values from props
        return {
            startDate: prevState.startDate || toMoment(startDate),
            endDate: prevState.endDate || toMoment(endDate),
            ...prevState
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
        if (current) {
            return current.isBefore(moment(), 'day');
        }
    }

    render() {
        const {isRange, handleClose, disabledDate} = this.props;
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
                                   disabledDate={disabledDate || this.disabledDate}
                                   format={_formatDateStr}
                                   {...props} />
                ) : (
                    <RCCalendar selectedValue={startDate}
                                onSelect={async (date) => {
                                    await this.setDates(date, null);
                                    handleClose();
                                }}
                                disabledDate={disabledDate || this.disabledDate}
                                format={_formatDateStr}
                                {...props} />
                ) }
            </div>
        );
    }
}
