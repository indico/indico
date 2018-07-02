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
import PropTypes from 'prop-types';
import React from 'react';
import RCCalendar from 'rc-calendar';
import RangeCalendar from 'rc-calendar/lib/RangeCalendar';
import DatePicker from 'rc-calendar/lib/Picker';
import {Button, Form, Grid, Select, Statistic} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {sanitizeRecurrence, serializeTime} from '../../util';
import TimeRangePicker from '../TimeRangePicker';

import './Landing.module.scss';


const _formatDateStr = 'YYYY-MM-DD';
const _serializeDate = date => (date ? date.format(_formatDateStr) : null);


export default class Landing extends React.Component {
    static propTypes = {
        setFilterParameter: PropTypes.func.isRequired,
        setFilters: PropTypes.func.isRequired
    };

    constructor(props) {
        super(props);
        const startTime = moment().startOf('hour').add(1, 'h');
        this.state = {
            recurrence: {
                type: 'single',
                number: 1,
                interval: 'week'
            },
            dates: {
                startDate: moment(),
                endDate: null
            },
            timeSlot: {
                startTime,
                endTime: startTime.clone().add(1, 'h')
            }
        };
    }

    updateBookingType = (newType) => {
        const {recurrence: {number, interval}} = this.state;
        const newState = {...this.state, recurrence: {type: newType, number, interval}};
        sanitizeRecurrence(newState);
        this.setState(newState);
    };

    updateNumber = (number) => {
        const {recurrence: {type, interval}} = this.state;
        this.setState({number});
        this.setState({
            recurrence: {type, number: parseInt(number, 10), interval}
        });
    };

    updateInterval = (interval) => {
        const {recurrence: {type, number}} = this.state;
        this.setState({
            recurrence: {type, number, interval}
        });
    };

    updateTimes = (startTime, endTime) => {
        this.setState({
            timeSlot: {
                startTime,
                endTime
            }
        });
    };

    updateDates = (startDate, endDate) => {
        this.setState({
            dates: {
                startDate,
                endDate
            }
        });
    };

    updateText = (value) => {
        const {setFilterParameter} = this.props;
        setFilterParameter('text', value);
    };

    disabledDate = (current) => {
        if (current) {
            return current.isBefore(moment(), 'day');
        }
    };

    doSearch = () => {
        const {
            timeSlot: {startTime, endTime},
            dates: {startDate, endDate},
            recurrence
        } = this.state;
        const {setFilters} = this.props;
        setFilters({
            recurrence,
            dates: {
                startDate: _serializeDate(startDate),
                endDate: _serializeDate(endDate)
            },
            timeSlot: {
                startTime: serializeTime(startTime),
                endTime: serializeTime(endTime)
            },
            equipment: {}
        });
    };

    render() {
        const {
            timeSlot: {startTime, endTime},
            dates: {startDate, endDate},
            recurrence: {type, number, interval}
        } = this.state;

        const calendar = (
            <RCCalendar selectedValue={startDate}
                        onSelect={(date) => this.updateDates(date, null)}
                        disabledDate={this.disabledDate}
                        format={_formatDateStr} />
        );

        const rangeCalendar = (
            <RangeCalendar onSelect={([start, end]) => this.updateDates(start, end)}
                           selectedValue={[startDate, endDate]}
                           disabledDate={this.disabledDate}
                           format={_formatDateStr} />
        );

        const recurrenceOptions = [
            {text: Translate.string('Weeks'), value: 'week'},
            {text: Translate.string('Months'), value: 'month'}
        ];

        return (
            <div className="landing-wrapper">
                <Grid centered styleName="landing-page">
                    <Grid.Row columns={2} styleName="landing-page-form">
                        <Grid.Column width={6} textAlign="center" verticalAlign="middle">
                            <Form>
                                <Form.Group inline>
                                    <Form.Radio label={Translate.string('Single booking')}
                                                name="type"
                                                value="single"
                                                checked={type === 'single'}
                                                onChange={(e, {value}) => this.updateBookingType(value)} />
                                    <Form.Radio label={Translate.string('Daily booking')}
                                                name="type"
                                                value="daily"
                                                checked={type === 'daily'}
                                                onChange={(e, {value}) => this.updateBookingType(value)} />
                                    <Form.Radio label={Translate.string('Recurring booking')}
                                                name="bookingType"
                                                value="every"
                                                checked={type === 'every'}
                                                onChange={(e, {value}) => this.updateBookingType(value)} />
                                </Form.Group>
                                {type === 'every' && (
                                    <Form.Group inline>
                                        <label>{Translate.string('Every')}</label>
                                        <Form.Input value={number} type="number" onChange={(event, data) => this.updateNumber(data.value)} />
                                        <Select value={interval} options={recurrenceOptions}
                                                onChange={(event, data) => this.updateInterval(data.value)} />
                                    </Form.Group>
                                )}
                                {['every', 'daily'].includes(type) && (
                                    <Form.Group inline>
                                        <DatePicker calendar={rangeCalendar}>
                                            {
                                                () => (
                                                    <Form.Group inline>
                                                        <Form.Input styleName="booking-date" icon="calendar" value={_serializeDate(startDate) || ''} />
                                                        <Form.Input styleName="booking-date" icon="calendar" value={_serializeDate(endDate) || ''} />
                                                    </Form.Group>
                                                )
                                            }
                                        </DatePicker>
                                    </Form.Group>
                                )}
                                {type === 'single' && (
                                    <DatePicker calendar={calendar}>
                                        {
                                            () => (
                                                <Form.Group inline>
                                                    <Form.Input styleName="booking-date" icon="calendar"
                                                                value={_serializeDate(startDate) || ''} />
                                                </Form.Group>
                                            )
                                        }
                                    </DatePicker>
                                )}
                                <Form.Group inline>
                                    <TimeRangePicker startTime={startTime}
                                                     endTime={endTime}
                                                     onChange={this.updateTimes} />
                                </Form.Group>
                                <Form.Group inline>
                                    <Form.Input icon="search" placeholder="bldg: 28" styleName="search-input"
                                                onChange={(event, data) => this.updateText(data.value)} />
                                </Form.Group>
                                <Button primary onClick={this.doSearch}>
                                    {Translate.string('Search')}
                                </Button>
                            </Form>
                        </Grid.Column>
                    </Grid.Row>
                    <Grid.Row>
                        <div styleName="statistics">
                            <Statistic size="huge">
                                <Statistic.Value>
                                    230
                                </Statistic.Value>
                                <Statistic.Label>
                                    {Translate.string('Active rooms')}
                                </Statistic.Label>
                            </Statistic>
                            <Statistic size="huge">
                                <Statistic.Value>
                                    70
                                </Statistic.Value>
                                <Statistic.Label>
                                    {Translate.string('Buildings')}
                                </Statistic.Label>
                            </Statistic>
                            <Statistic size="huge">
                                <Statistic.Value>
                                    25
                                </Statistic.Value>
                                <Statistic.Label>
                                    {Translate.string('Bookings today')}
                                </Statistic.Label>
                            </Statistic>
                            <Statistic size="huge">
                                <Statistic.Value>
                                    20
                                </Statistic.Value>
                                <Statistic.Label>
                                    {Translate.string('Active booking requests')}
                                </Statistic.Label>
                            </Statistic>
                        </div>
                    </Grid.Row>
                </Grid>
            </div>
        );
    }
}
