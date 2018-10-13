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
import RCCalendar from 'rc-calendar';
import {Button} from 'semantic-ui-react';
import moment from 'moment';
import DatePicker from 'rc-calendar/lib/Picker';
import {Translate} from 'indico/react/i18n';
import {toMoment} from 'indico/utils/date';
import TimelineLegend from './TimelineLegend';
import {legendLabelShape} from '../../props';
import {isDateWithinRange} from '../../util';


export default class TimelineHeader extends React.Component {
    static propTypes = {
        activeDate: PropTypes.instanceOf(moment).isRequired,
        onDateChange: PropTypes.func.isRequired,
        legendLabels: PropTypes.arrayOf(legendLabelShape).isRequired,
        dateRange: PropTypes.array,
        isLoading: PropTypes.bool,
        disableDatePicker: PropTypes.bool,
        mode: PropTypes.string,
        setMode: PropTypes.func.isRequired
    };

    static defaultProps = {
        isLoading: false,
        dateRange: [],
        disableDatePicker: false,
        mode: 'days'
    };

    calendarDisabledDate = (date) => {
        const {dateRange} = this.props;
        if (!date) {
            return false;
        }
        return dateRange.length !== 0 && !isDateWithinRange(date, dateRange, toMoment);
    };

    onSelect = (date) => {
        const {dateRange, onDateChange} = this.props;
        const freeRange = dateRange.length === 0;
        if (freeRange || isDateWithinRange(date, dateRange, toMoment)) {
            onDateChange(date);
        }
    };

    changeSelectedDate = (direction) => {
        const {activeDate, dateRange, onDateChange, mode} = this.props;
        const step = direction === 'next' ? 1 : -1;

        // dateRange is not set (unlimited)
        if (dateRange.length === 0 || mode !== 'days') {
            onDateChange(activeDate.clone().add(step, mode));
        } else {
            const index = dateRange.findIndex((dt) => toMoment(dt).isSame(activeDate)) + step;
            onDateChange(toMoment(dateRange[index]));
        }
    };

    renderModeSwitcher() {
        const {setMode, mode} = this.props;
        return !!mode && (
            <Button.Group size="small" style={{marginRight: 10}}>
                <Button content={Translate.string('Day')}
                        onClick={() => setMode('days')}
                        primary={mode === 'days'} />
                <Button content={Translate.string('Week')}
                        onClick={() => setMode('weeks')}
                        primary={mode === 'weeks'} />
                <Button content={Translate.string('Month')}
                        onClick={() => setMode('months')}
                        primary={mode === 'months'} />
            </Button.Group>
        );
    }

    renderDateSwitcher = () => {
        const {activeDate, dateRange, disableDatePicker, isLoading, mode} = this.props;
        const startDate = toMoment(dateRange[0]);
        const endDate = toMoment(dateRange[dateRange.length - 1]);
        const calendar = (
            <RCCalendar disabledDate={this.calendarDisabledDate}
                        onChange={this.onSelect}
                        value={activeDate} />
        );
        const prevDisabled = isLoading || activeDate.clone().subtract(1, mode).isBefore(startDate);
        const nextDisabled = isLoading || activeDate.clone().add(1, mode).isAfter(endDate);
        return (
            !disableDatePicker && (
                <div>
                    {this.renderModeSwitcher()}
                    <Button.Group size="small">
                        <Button icon="left arrow"
                                onClick={() => this.changeSelectedDate('prev')}
                                disabled={prevDisabled} />
                        <DatePicker calendar={calendar} disabled={isLoading || (prevDisabled && nextDisabled)}>
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
                                disabled={nextDisabled} />
                    </Button.Group>
                </div>
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
