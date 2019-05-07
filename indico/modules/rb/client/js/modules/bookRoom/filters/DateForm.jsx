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
import PropTypes from 'prop-types';
import {CalendarSingleDatePicker, CalendarRangeDatePicker} from 'indico/react/components';
import {serializeDate, toMoment} from 'indico/utils/date';
import {FilterFormComponent} from '../../../common/filters';


export default class DateForm extends FilterFormComponent {
    static propTypes = {
        startDate: PropTypes.string,
        endDate: PropTypes.string,
        isRange: PropTypes.bool.isRequired,
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
            setParentField('startDate', serializeDate(startDate));
            setParentField('endDate', serializeDate(endDate));
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
        const {isRange, disabledDate} = this.props;
        const {startDate, endDate} = this.state;
        return isRange ? (
            <CalendarRangeDatePicker startDate={startDate}
                                     endDate={endDate}
                                     onDatesChange={async ({startDate: sd, endDate: ed}) => {
                                         await this.setDates(sd, ed);
                                     }}
                                     disabledDate={disabledDate || this.disabledDate}
                                     noBorder />
        ) : (
            <CalendarSingleDatePicker date={startDate}
                                      onDateChange={async (date) => {
                                          await this.setDates(date, null);
                                      }}
                                      disabledDate={disabledDate || this.disabledDate}
                                      noBorder />
        );
    }
}
