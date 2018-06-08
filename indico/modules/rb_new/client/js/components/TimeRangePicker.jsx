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
import propTypes from 'prop-types';
import {Dropdown} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {toMoment} from '../util';

import './TimeRangePicker.module.scss';


const _serializeTime = time => (time ? time.format('HH:mm') : null);

function _humanizeDuration(duration) {
    const hours = duration.hours();
    const minutes = duration.minutes();
    if (hours === 1 && minutes === 0) {
        return Translate.string('1 hour');
    } else if (hours !== 0) {
        return Translate.string('{time} hours', {time: hours + (minutes / 60)});
    } else {
        return Translate.string('{time} minutes', {time: minutes});
    }
}

export default class TimeRangePicker extends React.Component {
    static propTypes = {
        startTime: propTypes.object,
        endTime: propTypes.object,
        onChange: propTypes.func.isRequired,
    };

    static defaultProps = {
        startTime: moment().startOf('hour').add(1, 'h'),
        endTime: moment().startOf('hour').add(2, 'h')
    };

    constructor(props) {
        super(props);

        const {startTime, endTime} = this.props;
        const startOptions = this.generateStartTimeOptions();
        const endOptions = this.generateEndTimeOptions(startTime);
        const duration = moment.duration(endTime.diff(startTime));
        this.addOptionIfMissing(startOptions, _serializeTime(moment(startTime)));
        this.addOptionIfMissing(endOptions, _serializeTime(moment(endTime)));
        this.state = {
            startTime,
            endTime,
            startOptions,
            endOptions,
            duration
        };
    }

    generateStartTimeOptions = () => {
        const options = [];
        const end = moment().endOf('day');
        const next = moment().startOf('day');
        let serializedNext;
        while (next < end) {
            serializedNext = _serializeTime(moment(next));
            options.push({key: serializedNext, value: serializedNext, text: serializedNext});
            next.add(30, 'm');
        }
        return options;
    };

    generateEndTimeOptions = (start) => {
        const options = [];
        const end = moment().endOf('day');
        const next = moment(start).add(30, 'm');
        let serializedNext, duration, text;
        while (next < end) {
            duration = _humanizeDuration(moment.duration(next.diff(start)));
            serializedNext = _serializeTime(moment(next));
            text = <div>{serializedNext} <div styleName="duration">({duration})</div></div>;
            options.push({key: serializedNext, value: serializedNext, text});
            next.add(30, 'm');
        }
        return options;
    };

    addOptionIfMissing = (options, value) => {
        const found = options.some((el) => {
            return el.value === value;
        });
        if (!found) {
            options.unshift({key: value, value, text: value});
            return true;
        }
        return false;
    };

    updateStartTime = (startTime, endTime, duration) => {
        const start = moment(startTime, ['HH:mm', 'HHmm', 'Hmm']);
        let end = toMoment(endTime, 'HH:mm');
        if (start.isValid()) {
            if (end <= start) {
                end = moment(start).add(duration);
                if (end > moment().endOf('day')) {
                    end = moment().endOf('day');
                }
            } else {
                duration = moment.duration(end.diff(start));
            }
            const startOptions = this.generateStartTimeOptions();
            const endOptions = this.generateEndTimeOptions(start);
            this.addOptionIfMissing(startOptions, _serializeTime(moment(start)));
            this.addOptionIfMissing(endOptions, _serializeTime(moment(end)));
            this.setState({
                startTime: start,
                endTime: end,
                duration,
                startOptions,
                endOptions
            });
            const {onChange} = this.props;
            onChange(start, end);
        }
    };

    updateEndTime = (startTime, endTime, duration) => {
        let start = toMoment(startTime, 'HH:mm');
        const end = moment(endTime, ['HH:mm', 'HHmm', 'Hmm']);
        if (end.isValid()) {
            if (end <= start) {
                start = moment(end).subtract(duration);
                if (start < moment().startOf('day')) {
                    start = moment().startOf('day');
                }
            } else {
                duration = moment.duration(end.diff(start));
            }
            const startOptions = this.generateStartTimeOptions();
            const endOptions = this.generateEndTimeOptions(start);
            this.addOptionIfMissing(startOptions, _serializeTime(moment(start)));
            this.addOptionIfMissing(endOptions, _serializeTime(moment(end)));
            this.setState({
                startTime: start,
                endTime: end,
                duration,
                startOptions,
                endOptions,
            });
            const {onChange} = this.props;
            onChange(start, end);
        }
    };

    render() {
        const {startTime, endTime, startOptions, endOptions, duration} = this.state;
        return (
            <div>
                <Dropdown options={startOptions}
                          search={() => []}
                          icon={null}
                          text={_serializeTime(startTime)}
                          selection
                          allowAdditions
                          additionLabel=""
                          styleName="time-dropdown"
                          value={_serializeTime(startTime)}
                          onChange={(_, {value}) => {
                              this.updateStartTime(value, endTime, duration);
                          }} />
                <Dropdown options={endOptions}
                          search={() => []}
                          icon={null}
                          text={_serializeTime(endTime)}
                          selection
                          allowAdditions
                          additionLabel=""
                          styleName="time-dropdown"
                          value={_serializeTime(endTime)}
                          onChange={(_, {value}) => {
                              this.updateEndTime(startTime, value, duration);
                          }} />
            </div>
        );
    }
}
