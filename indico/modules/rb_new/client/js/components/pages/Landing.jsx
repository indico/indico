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
import {Link} from 'react-router-dom';
import Calendar from 'rc-calendar';
import RangeCalendar from 'rc-calendar/lib/RangeCalendar';
import DatePicker from 'rc-calendar/lib/Picker';
import TimePicker from 'rc-time-picker';
import {Button, Grid, Form, Select} from 'semantic-ui-react';
import _ from 'lodash';
import {toMoment} from '../../util';

import './Landing.module.scss';


const _serializeTime = time => (time ? time.format('HH:mm') : null);


export default class Landing extends React.Component {
    static getDerivedStateFromProps({
        recurrence: {type, interval, number},
        dates: {startDate, endDate},
        timeSlot: {startTime, endTime}
    }, prevState) {
        return {
            ...prevState,
            ..._.omitBy({
                bookingType: type,
                interval,
                number,
                startDate: startDate,
                endDate: endDate,
                startTime: toMoment(startTime, 'HH:mm'),
                endTime: toMoment(endTime, 'HH:mm')
            }, _.isNull)};
    }

    constructor(props) {
        super(props);
        this.state = {};
    }

    componentDidMount() {
        const {setFilterParameter} = this.props;
        const startTime = moment().endOf('hour').add(1, 'm');
        setFilterParameter('recurrence', {
            type: 'single'
        });
        setFilterParameter('dates', {
            startDate: moment().format('YYYY-MM-DD')
        });
        setFilterParameter('timeSlot', {
            startTime: _serializeTime(startTime),
            endTime: _serializeTime(startTime.clone().add(1, 'h'))
        });
    }

    updateBookingType = (newType) => {
        const {setFilterParameter} = this.props;
        const {bookingType} = this.state;
        let {number, interval} = this.state;

        if (newType === 'every' && bookingType !== newType) {
            number = 1;
            interval = 'week';
        }

        setFilterParameter('recurrence', {type: newType, number, interval});
    }

    updateNumber = (number) => {
        const {setFilterParameter} = this.props;
        this.setState({number});
        setFilterParameter('recurrence', {type: 'every', number: parseInt(number, 10), interval: null});
    }

    updateInterval = (interval) => {
        const {setFilterParameter} = this.props;
        this.setState({interval});
        setFilterParameter('recurrence', {type: 'every', number: parseInt(this.state.number, 10), interval});
    }

    updateTimes = (startTime, endTime) => {
        const {setFilterParameter} = this.props;
        this.setState({startTime, endTime});

        setFilterParameter('timeSlot', {
            startTime: startTime ? startTime.format('HH:mm') : null,
            endTime: endTime ? endTime.format('HH:mm') : null
        });
    }

    updateDates = (startDate, endDate) => {
        const {setFilterParameter} = this.props;
        this.setState({
            startDate: startDate ? startDate.format('YYYY-MM-DD') : null,
            endDate: endDate ? endDate.format('YYYY-MM-DD') : null
        });

        setFilterParameter('dates', {
            startDate: startDate ? startDate.format('YYYY-MM-DD') : null,
            endDate: endDate ? endDate.format('YYYY-MM-DD') : null
        });
    }

    updateText = (value) => {
        const {setFilterParameter} = this.props;
        setFilterParameter('text', value);
    }

    render() {
        const {bookingType, startTime, endTime, startDate, endDate, number, interval} = this.state;
        const timePickerProps = {
            minuteStep: 5,
            format: 'HH:mm',
            allowEmpty: false,
            showSecond: false
        };

        return (
            <Grid centered styleName="landing-page">
                <Grid.Row columns={2} styleName="landing-page-form">
                    <Grid.Column width={4} textAlign="center" verticalAlign="middle">
                        <Form>
                            <Form.Group inline>
                                <Form.Radio label="Single booking"
                                            name="bookingType"
                                            value="single"
                                            checked={bookingType === 'single'}
                                            onChange={(e, {value}) => this.updateBookingType(value)}/>
                                <Form.Radio label="Recurring booking"
                                            name="bookingType"
                                            value="every"
                                            checked={bookingType === 'every'}
                                            onChange={(e, {value}) => this.updateBookingType(value)}/>
                            </Form.Group>
                            {bookingType === 'every' &&
                                <>
                                    <Form.Group inline>
                                        <label>Every</label>
                                        <Form.Input value={number} type="number" onChange={(event, data) => this.updateNumber(data.value)}/>
                                        <Select value={interval} options={[{text: 'Days', value: 'day'}, {text: 'Weeks', value: 'week'}, {text: 'Months', value: 'month'}]}
                                                onChange={(event, data) => this.updateInterval(data.value)} />
                                    </Form.Group>
                                    <Form.Group inline>
                                        <DatePicker calendar={<RangeCalendar
                                                                    onSelect={([start, end]) => {
                                                                        this.updateDates(start, end);
                                                                    }}
                                                                    selectedValue={[startDate, endDate]} />}>
                                            {
                                                () => {
                                                    return (
                                                        <Form.Group inline>
                                                            <Form.Input icon="calendar" style={{width: 250}} value={startDate || ''}/>
                                                            <Form.Input icon="calendar" style={{width: 250}} value={endDate || ''} />
                                                        </Form.Group>
                                                    );
                                                }
                                            }
                                        </DatePicker>
                                    </Form.Group>
                                </>
                            }
                            {bookingType !== 'every' &&
                                <DatePicker calendar={<Calendar />}
                                            onChange={(value) => this.updateDates(value, null)}>
                                    {
                                        () => {
                                            return (
                                                <Form.Input icon="calendar" style={{width: 250}} value={startDate || ''} />
                                            );
                                        }
                                    }
                                </DatePicker>
                            }
                            <Form.Group inline>
                                <TimePicker {...timePickerProps} value={startTime}
                                            onChange={(value) => {this.updateTimes(value, endTime)}} />
                                -
                                <TimePicker {...timePickerProps} value={endTime}
                                            onChange={(value) => {this.updateTimes(startTime, value)}} />
                            </Form.Group>
                            <Form.Input icon="search" placeholder="bldg: 28" style={{width: 300}}
                                        onChange={(event, data) => this.updateText(data.value)} />
                            <Link to="/book">
                                <Button primary>Search</Button>
                            </Link>
                        </Form>
                    </Grid.Column>
                </Grid.Row>
            </Grid>
        );
    }
}
