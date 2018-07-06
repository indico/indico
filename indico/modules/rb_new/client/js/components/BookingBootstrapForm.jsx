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

import PropTypes from 'prop-types';
import React from 'react';
import {Button, Form, Select} from 'semantic-ui-react';
import RCCalendar from 'rc-calendar';
import RangeCalendar from 'rc-calendar/lib/RangeCalendar';
import DatePicker from 'rc-calendar/lib/Picker';
import {Translate} from 'indico/react/i18n';
import TimeRangePicker from './TimeRangePicker';
import {sanitizeRecurrence, serializeTime} from '../util';

import './BookingBootstrapForm.module.scss';


const _formatDateStr = 'YYYY-MM-DD';
const _serializeDate = date => (date ? date.format(_formatDateStr) : null);

export default class BookingBootstrapForm extends React.Component {
    static propTypes = {
        onSearch: PropTypes.func.isRequired,
        onChange: PropTypes.func,
        buttonCaption: PropTypes.object,
        children: PropTypes.node,
        buttonDisabled: PropTypes.bool
    };

    static defaultProps = {
        children: null,
        buttonCaption: <Translate>Search</Translate>,
        onChange: () => {},
        buttonDisabled: false
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

    componentDidMount() {
        this.triggerChange();
    }

    triggerChange() {
        const {onChange} = this.props;
        onChange(this.serializedState);
    }

    updateDates = (startDate, endDate) => {
        this.setState({
            dates: {
                startDate,
                endDate
            }
        }, () => {
            this.triggerChange();
        });
    };

    updateBookingType = (newType) => {
        const {recurrence: {number, interval}} = this.state;
        const newState = {...this.state, recurrence: {type: newType, number, interval}};
        sanitizeRecurrence(newState);
        this.setState(newState, () => {
            this.triggerChange();
        });
    };

    updateNumber = (number) => {
        const {recurrence: {type, interval}} = this.state;
        this.setState({number});
        this.setState({
            recurrence: {type, number: parseInt(number, 10), interval}
        }, () => {
            this.triggerChange();
        });
    };

    updateInterval = (interval) => {
        const {recurrence: {type, number}} = this.state;
        this.setState({
            recurrence: {type, number, interval}
        }, () => {
            this.triggerChange();
        });
    };

    updateTimes = (startTime, endTime) => {
        this.setState({
            timeSlot: {
                startTime,
                endTime
            }
        }, () => {
            this.triggerChange();
        });
    };

    get serializedState() {
        const {
            timeSlot: {startTime, endTime},
            dates: {startDate, endDate},
            recurrence
        } = this.state;

        return {
            recurrence,
            dates: {
                startDate: _serializeDate(startDate),
                endDate: _serializeDate(endDate)
            },
            timeSlot: {
                startTime: serializeTime(startTime),
                endTime: serializeTime(endTime)
            },
        };
    }

    onSearch = () => {
        const {onSearch} = this.props;
        onSearch(this.serializedState);
    };

    render() {
        const {
            timeSlot: {startTime, endTime},
            recurrence: {type, number, interval},
            dates: {startDate, endDate}
        } = this.state;

        const {buttonCaption, buttonDisabled, children} = this.props;

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
                                name="type"
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
                {children}
                <Button primary disabled={buttonDisabled} onClick={this.onSearch}>
                    {buttonCaption}
                </Button>
            </Form>
        );
    }
}
