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
import PropTypes from 'prop-types';
import Calendar from 'rc-calendar';
import {Button} from 'semantic-ui-react';
import moment from 'moment';
import DatePicker from 'rc-calendar/lib/Picker';
import {toMoment} from 'indico/utils/date';
import TimelineLegend from './TimelineLegend';
import {legendLabelShape} from '../props';
import {isDateWithinRange} from '../util';


export default class TimelineHeader extends React.Component {
    static propTypes = {
        activeDate: PropTypes.instanceOf(moment).isRequired,
        onDateChange: PropTypes.func.isRequired,
        legendLabels: PropTypes.arrayOf(legendLabelShape).isRequired,
        dateRange: PropTypes.array,
        isLoading: PropTypes.bool,
        disableDatePicker: PropTypes.bool,
    };

    static defaultProps = {
        isLoading: false,
        dateRange: [],
        disableDatePicker: false,
    };

    calendarDisabledDate = (date) => {
        const {dateRange} = this.props;
        if (!date) {
            return false;
        }
        return dateRange.length !== 0 && !isDateWithinRange(date, dateRange, toMoment);
    };

    changeSelectedDate = (mode) => {
        const {activeDate, dateRange, onDateChange} = this.props;
        const step = mode === 'next' ? 1 : -1;

        // dateRange is not set (unlimited)
        if (dateRange.length === 0) {
            onDateChange(activeDate.clone().add(step, 'day'));
        } else {
            const index = dateRange.findIndex((dt) => toMoment(dt).isSame(activeDate)) + step;
            onDateChange(toMoment(dateRange[index]));
        }
    };

    renderDateSwitcher = () => {
        const {activeDate, dateRange, disableDatePicker, isLoading} = this.props;
        const startDate = toMoment(dateRange[0]);
        const endDate = toMoment(dateRange[dateRange.length - 1]);
        const calendar = <Calendar disabledDate={this.calendarDisabledDate} onChange={this.onSelect} />;
        const freeRange = dateRange.length === 0;
        return (
            !disableDatePicker && (
                <Button.Group floated="right" size="small">
                    <Button icon="left arrow"
                            onClick={() => this.changeSelectedDate('prev')}
                            disabled={isLoading || (!freeRange && activeDate.clone().subtract(1, 'day').isBefore(startDate))} />
                    <DatePicker calendar={calendar} disabled={isLoading}>
                        {
                            () => (
                                <Button primary>
                                    {activeDate.format('L')}
                                </Button>
                            )
                        }
                    </DatePicker>
                    <Button icon="right arrow"
                            onClick={() => this.changeSelectedDate('next')}
                            disabled={isLoading || activeDate.clone().add(1, 'day').isAfter(endDate)} />
                </Button.Group>
            )
        );
    };

    render() {
        const {legendLabels} = this.props;
        return (
            <TimelineLegend labels={legendLabels} aside={this.renderDateSwitcher()} />
        );
    }
}
