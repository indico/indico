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

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {Button, Form, Select} from 'semantic-ui-react';
import {SingleDatePicker, DateRangePicker} from 'indico/react/components';
import {PluralTranslate, Translate} from 'indico/react/i18n';
import {Overridable} from 'indico/react/util';
import {serializeDate, serializeTime} from 'indico/utils/date';
import TimeRangePicker from './TimeRangePicker';
import {sanitizeRecurrence} from '../util';


class BookingBootstrapForm extends React.Component {
    static propTypes = {
        onSearch: PropTypes.func.isRequired,
        onChange: PropTypes.func,
        buttonCaption: PropTypes.object,
        children: PropTypes.node,
        buttonDisabled: PropTypes.bool,
        dayBased: PropTypes.bool,
        onlyDaily: PropTypes.bool,
        defaults: PropTypes.object,
    };

    static get defaultProps() {
        return {
            children: null,
            buttonCaption: <Translate>Search</Translate>,
            onChange: () => {},
            buttonDisabled: false,
            dayBased: false,
            onlyDaily: false,
            defaults: {},
        };
    }

    constructor(props) {
        super(props);

        const {defaults} = props;
        this.state = _.merge({
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
                startTime: moment().startOf('hour').add(1, 'h'),
                endTime: moment().startOf('hour').add(2, 'h')
            }
        }, defaults);
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
        const {dayBased} = this.props;
        const {
            timeSlot: {startTime, endTime},
            dates: {startDate, endDate},
            recurrence
        } = this.state;

        const state = {
            recurrence,
            dates: {
                startDate: serializeDate(startDate),
                endDate: serializeDate(endDate)
            }
        };

        if (!dayBased) {
            state.timeSlot = {
                startTime: serializeTime(startTime),
                endTime: serializeTime(endTime)
            };
        }
        return state;
    }

    onSearch = e => {
        const {onSearch} = this.props;
        onSearch(this.serializedState);
        e.preventDefault();
    };

    render() {
        const {
            timeSlot: {startTime, endTime},
            recurrence: {type, number, interval},
            dates: {startDate, endDate}
        } = this.state;

        const {buttonCaption, buttonDisabled, children, dayBased, onlyDaily} = this.props;
        const recurrenceOptions = [
            {text: PluralTranslate.string('Week', 'Weeks', number), value: 'week'},
            {text: PluralTranslate.string('Month', 'Months', number), value: 'month'}
        ];

        return (
            <Form>
                <Form.Group inline>
                    {!onlyDaily && (
                        <Form.Radio label={Translate.string('Single booking')}
                                    name="type"
                                    value="single"
                                    checked={type === 'single'}
                                    onChange={(e, {value}) => this.updateBookingType(value)} />
                    )}
                    <Form.Radio label={Translate.string('Daily booking')}
                                name="type"
                                value="daily"
                                checked={type === 'daily'}
                                onChange={(e, {value}) => this.updateBookingType(value)} />
                    {!onlyDaily && (
                        <Form.Radio label={Translate.string('Recurring booking')}
                                    name="type"
                                    value="every"
                                    checked={type === 'every'}
                                    onChange={(e, {value}) => this.updateBookingType(value)} />
                    )}
                </Form.Group>
                {type === 'every' && (
                    <Form.Group inline>
                        <label>{Translate.string('Every')}</label>
                        <Form.Input type="number"
                                    value={number}
                                    min="1"
                                    max="99"
                                    step="1"
                                    onChange={(event, data) => this.updateNumber(data.value)} />
                        <Select value={interval} options={recurrenceOptions}
                                onChange={(event, data) => this.updateInterval(data.value)} />
                    </Form.Group>
                )}
                {['every', 'daily'].includes(type) && (
                    <DateRangePicker startDate={startDate}
                                     endDate={endDate}
                                     onDatesChange={({startDate: sd, endDate: ed}) => this.updateDates(sd, ed)} />

                )}
                {type === 'single' && (
                    <SingleDatePicker date={startDate} onDateChange={(date) => this.updateDates(date, null)} />
                )}
                {!dayBased && (
                    <Form.Group inline>
                        <TimeRangePicker startTime={startTime}
                                         endTime={endTime}
                                         onChange={this.updateTimes} />
                    </Form.Group>
                )}
                {children}
                <Button primary disabled={buttonDisabled} onClick={this.onSearch}>
                    {buttonCaption}
                </Button>
            </Form>
        );
    }
}

export default Overridable.component('BookingBootstrapForm', BookingBootstrapForm);
