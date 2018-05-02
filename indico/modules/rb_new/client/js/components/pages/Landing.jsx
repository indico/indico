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
import {Link} from 'react-router-dom';
import Calendar from 'rc-calendar';
import RangeCalendar from 'rc-calendar/lib/RangeCalendar';
import DatePicker from 'rc-calendar/lib/Picker';
import TimePicker from 'rc-time-picker';
import {Button, Grid, Form, Select} from 'semantic-ui-react';
import {stateToQueryString} from 'redux-router-querystring';
import {Translate} from 'indico/react/i18n';
import {sanitizeRecurrence} from '../../util';
import {queryString as qsRules} from '../../serializers/filters';

import './Landing.module.scss';


const _serializeTime = time => (time ? time.format('HH:mm') : null);
const _serializeDate = date => (date ? date.format('YYYY-MM-DD') : null);


export default class Landing extends React.Component {
    static propTypes = {
        setFilterParameter: PropTypes.func.isRequired
    };

    constructor(props) {
        super(props);
        const startTime = moment().endOf('hour').add(1, 'm');
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

    render() {
        const {
            timeSlot: {startTime, endTime},
            dates: {startDate, endDate},
            recurrence, recurrence: {type, number, interval}
        } = this.state;

        const timePickerProps = {
            minuteStep: 5,
            format: 'HH:mm',
            allowEmpty: false,
            showSecond: false
        };

        const targetQS = stateToQueryString({
            filters: {
                recurrence,
                dates: {
                    startDate: _serializeDate(startDate),
                    endDate: _serializeDate(endDate)
                },
                timeSlot: {
                    startTime: _serializeTime(startTime),
                    endTime: _serializeTime(endTime)
                }
            }
        }, qsRules);

        const rangeCalendar = (
            <RangeCalendar onSelect={([start, end]) => this.updateDates(start, end)}
                           selectedValue={[startDate, endDate]} />
        );

        const recurrenceOptions = [
            {text: Translate.string('Days'), value: 'day'},
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
                                    <Form.Radio label={Translate.string('Recurring booking')}
                                                name="bookingType"
                                                value="every"
                                                checked={type === 'every'}
                                                onChange={(e, {value}) => this.updateBookingType(value)} />
                                </Form.Group>
                                {type === 'every' &&
                                    <>
                                        <Form.Group inline>
                                            <label>{Translate.string('Every')}</label>
                                            <Form.Input value={number} type="number" onChange={(event, data) => this.updateNumber(data.value)} />
                                            <Select value={interval} options={recurrenceOptions}
                                                    onChange={(event, data) => this.updateInterval(data.value)} />
                                        </Form.Group>
                                        <Form.Group inline>
                                            <DatePicker calendar={rangeCalendar}>
                                                {
                                                    () => {
                                                        return (
                                                            <Form.Group inline>
                                                                <Form.Input styleName="booking-date" icon="calendar" value={_serializeDate(startDate) || ''} />
                                                                <Form.Input styleName="booking-date" icon="calendar" value={_serializeDate(endDate) || ''} />
                                                            </Form.Group>
                                                        );
                                                    }
                                                }
                                            </DatePicker>
                                        </Form.Group>
                                    </>
                                }
                                {type !== 'every' && (
                                    <DatePicker calendar={<Calendar />}
                                                onChange={(value) => this.updateDates(value, null)}>
                                        {
                                            () => {
                                                return (
                                                    <Form.Group inline>
                                                        <Form.Input styleName="booking-date" icon="calendar"
                                                                    value={_serializeDate(startDate) || ''} />
                                                    </Form.Group>
                                                );
                                            }
                                        }
                                    </DatePicker>
                                )}
                                <Form.Group inline>
                                    <TimePicker {...timePickerProps} value={startTime}
                                                onChange={(value) => this.updateTimes(value, endTime)} />
                                    -
                                    <TimePicker {...timePickerProps} value={endTime}
                                                onChange={(value) => this.updateTimes(startTime, value)} />
                                </Form.Group>
                                <Form.Group inline>
                                    <Form.Input icon="search" placeholder="bldg: 28" styleName="search-input"
                                                onChange={(event, data) => this.updateText(data.value)} />
                                </Form.Group>
                                <Link to={{
                                    pathname: '/book',
                                    search: `?${targetQS}`
                                }}>
                                    <Button primary>
                                        {Translate.string('Search')}
                                    </Button>
                                </Link>
                            </Form>
                        </Grid.Column>
                    </Grid.Row>
                </Grid>
            </div>
        );
    }
}
