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
import React from 'react';
import PropTypes from 'prop-types';
import {Dropdown} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {serializeTime, toMoment, isBookingStartDTValid} from 'indico/utils/date';

import './TimeRangePicker.module.scss';


const ARROW_KEYS = ['ArrowUp', 'ArrowDown', 'Up', 'Down'];
const START_HOUR = '06:00';

function _humanizeDuration(duration) {
    const hours = duration.hours();
    const minutes = duration.minutes();
    if (hours === 1 && minutes === 0) {
        return Translate.string('1 hour');
    } else if (hours !== 0) {
        return Translate.string('{time} hours', {time: hours + (minutes / 60)});
    } else {
        return Translate.string('{time} min', {time: minutes});
    }
}

function generateStartTimeOptions(allowPastTimes, bookingGracePeriod) {
    const options = [];
    const end = moment().endOf('day');
    const next = moment(START_HOUR, 'HH:mm');

    // eslint-disable-next-line no-unmodified-loop-condition
    while (next < end) {
        const momentNext = moment(next);
        if (isBookingStartDTValid(momentNext, allowPastTimes, bookingGracePeriod)) {
            const serializedNext = serializeTime(momentNext);
            options.push({key: serializedNext, value: serializedNext, text: serializedNext});
        }
        next.add(30, 'm');
    }
    return options;
}

function generateEndTimeOptions(start) {
    const options = [];
    const end = moment().endOf('day');
    const next = moment(start).add(30, 'm');
    let duration;
    // eslint-disable-next-line no-unmodified-loop-condition
    while (next < end) {
        duration = _humanizeDuration(moment.duration(next.diff(start)));
        const serializedNext = serializeTime(moment(next));
        const text = (
            <div styleName="end-time-item">{serializedNext} <span styleName="duration">({duration})</span></div>
        );
        options.push({key: serializedNext, value: serializedNext, text});
        next.add(30, 'm');
    }
    return options;
}


export default class TimeRangePicker extends React.Component {
    static propTypes = {
        allowPastTimes: PropTypes.bool,
        startTime: PropTypes.object,
        endTime: PropTypes.object,
        onChange: PropTypes.func.isRequired,
        disabled: PropTypes.bool,
        bookingGracePeriod: PropTypes.number,
    };

    static defaultProps = {
        allowPastTimes: false,
        disabled: false,
        startTime: moment().startOf('hour').add(1, 'h'),
        endTime: moment().startOf('hour').add(2, 'h'),
        bookingGracePeriod: 1,
    };

    constructor(props) {
        super(props);

        const {startTime, endTime} = this.props;
        const duration = moment.duration(endTime.diff(startTime));
        const startSearchQuery = serializeTime(moment(startTime));
        const endSearchQuery = serializeTime(moment(endTime));
        this.state = {
            startTime,
            endTime,
            duration,
            startSearchQuery,
            endSearchQuery
        };
    }

    shouldComponentUpdate(nextProps, nextState) {
        return (nextState !== this.state || !_.isEqual(this.props, nextProps));
    }

    updateStartTime = (event, currentStartTime, previousStartTime, endTime, duration, startSearchQuery) => {
        if (event.type === 'keydown' && ARROW_KEYS.includes(event.key)) {
            this.setState({
                startSearchQuery: currentStartTime
            });
            return;
        }
        let start;
        const {allowPastTimes, onChange, bookingGracePeriod} = this.props;
        if (event.type === 'click') {
            start = moment(currentStartTime, ['HH:mm', 'Hmm']);
        } else {
            start = moment(startSearchQuery, ['HH:mm', 'Hmm']);
        }
        if (!start.isValid()) {
            this.setState({
                startSearchQuery: serializeTime(previousStartTime)
            });
            return;
        } else if (!isBookingStartDTValid(start, allowPastTimes, bookingGracePeriod)) {
            this.setState({
                startSearchQuery: serializeTime(previousStartTime)
            });
            return;
        }

        let end = toMoment(endTime, 'HH:mm');
        if (end.isSameOrBefore(start, 'minute')) {
            end = moment(start).add(duration);
            if (end > moment().endOf('day')) {
                end = moment().endOf('day');
                if (start.isSame(end, 'minute')) {
                    start = moment(end).subtract(duration);
                }
            }
        } else {
            duration = moment.duration(end.diff(start));
        }
        this.setState({
            startTime: start,
            endTime: end,
            startSearchQuery: serializeTime(start),
            endSearchQuery: serializeTime(end),
            duration,
        });
        onChange(start, end);
    };

    updateEndTime = (event, currentEndTime, previousEndTime, startTime, duration, endSearchQuery) => {
        if (event.type === 'keydown' && ARROW_KEYS.includes(event.key)) {
            this.setState({
                endSearchQuery: currentEndTime
            });
            return;
        }
        let end;
        if (event.type === 'click') {
            end = moment(currentEndTime, ['HH:mm', 'Hmm']);
        } else {
            end = moment(endSearchQuery, ['HH:mm', 'Hmm']);
        }
        if (!end.isValid()) {
            this.setState({
                endSearchQuery: serializeTime(previousEndTime)
            });
            return;
        }
        let start = toMoment(startTime, 'HH:mm');
        const {allowPastTimes, onChange, bookingGracePeriod} = this.props;
        if (!isBookingStartDTValid(end, allowPastTimes, bookingGracePeriod)) {
            this.setState({
                endSearchQuery: serializeTime(previousEndTime)
            });
            return;
        }
        if (end.isSameOrBefore(start, 'minute')) {
            start = moment(end).subtract(duration);
            if (start < moment().startOf('day')) {
                start = moment().startOf('day');
                if (end.isSame(start, 'minute')) {
                    end = moment(start).add(duration);
                }
            } else if (!isBookingStartDTValid(start, allowPastTimes, bookingGracePeriod)) {
                this.setState({
                    endSearchQuery: serializeTime(previousEndTime)
                });
                return;
            }
        } else {
            duration = moment.duration(end.diff(start));
        }
        this.setState({
            startTime: start,
            endTime: end,
            startSearchQuery: serializeTime(start),
            endSearchQuery: serializeTime(end),
            duration,
        });
        onChange(start, end);
    };

    onStartSearchChange = (event) => {
        this.setState({
            startSearchQuery: event.target.value
        });
    };

    onEndSearchChange = (event) => {
        this.setState({
            endSearchQuery: event.target.value
        });
    };

    render() {
        const {startTime, endTime, duration, startSearchQuery, endSearchQuery} = this.state;
        const {disabled, allowPastTimes, bookingGracePeriod} = this.props;
        const startOptions = generateStartTimeOptions(allowPastTimes, bookingGracePeriod);
        const endOptions = generateEndTimeOptions(startTime);
        return (
            <div styleName="time-range-picker">
                <Dropdown options={startOptions}
                          search={() => startOptions}
                          icon={null}
                          selection
                          styleName="start-time-dropdown"
                          searchQuery={startSearchQuery}
                          onSearchChange={this.onStartSearchChange}
                          value={serializeTime(startTime)}
                          disabled={disabled}
                          onChange={(event, {value}) => {
                              this.updateStartTime(event, value, startTime, endTime, duration, startSearchQuery);
                          }} />
                <Dropdown options={endOptions}
                          search={() => endOptions}
                          icon={null}
                          selection
                          styleName="end-time-dropdown"
                          searchQuery={endSearchQuery}
                          onSearchChange={this.onEndSearchChange}
                          value={serializeTime(endTime)}
                          disabled={disabled}
                          onChange={(event, {value}) => {
                              this.updateEndTime(event, value, endTime, startTime, duration, endSearchQuery);
                          }} />
            </div>
        );
    }
}
