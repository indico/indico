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
import {toMoment} from '../util';

import './TimeRangePicker.module.scss';


const _serializeTime = time => (time ? time.format('HH:mm') : null);

function generateTimeOptions(start = moment().startOf('day')) {
    const options = [];
    const startTime = moment(start).format('HH:mm');
    options.push({key: startTime, value: startTime, text: startTime});
    let next = moment(start).add(30, 'm');
    let nextTime = _serializeTime(moment(next));
    while (nextTime !== startTime) {
        options.push({key: nextTime, value: nextTime, text: nextTime});
        next = moment(next).add(30, 'm');
        nextTime = _serializeTime(moment(next));
    }
    return options;
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
        const startOptions = generateTimeOptions();
        const endOptions = generateTimeOptions();
        this.addOptionIfNotExist(startOptions, _serializeTime(moment(startTime)));
        this.addOptionIfNotExist(endOptions, _serializeTime(moment(endTime)));
        this.state = {
            startTime,
            endTime,
            startOptions,
            endOptions
        };
    }

    addOptionIfNotExist(options, value) {
        const found = options.some((el) => {
            return el.value === value;
        });
        if (!found) {
            options.push({key: value, value, text: value});
            return true;
        }
        return false;
    }

    setStartTime(startTime, endTime) {
        const start = moment(startTime, ['HH:mm', 'HHmm', 'Hmm']);
        const end = toMoment(endTime, 'HH:mm');
        if (start.isValid()) {
            const options = generateTimeOptions();
            const added = this.addOptionIfNotExist(options, _serializeTime(moment(start)));
            if (added) {
                this.updateOptions(options, true);
            }
            this.setState({
                startTime: start
            });
            const {onChange} = this.props;
            onChange(start, end);
        }
    }


    setEndTime(startTime, endTime) {
        const start = toMoment(startTime, 'HH:mm');
        const end = moment(endTime, ['HH:mm', 'HHmm', 'Hmm']);
        if (end.isValid()) {
            const options = generateTimeOptions();
            const added = this.addOptionIfNotExist(options, _serializeTime(moment(end)));
            if (added) {
                this.updateOptions(options, false);
            }
            this.setState({
                endTime: end
            });
            const {onChange} = this.props;
            onChange(start, end);
        }
    }

    updateOptions(options, start) {
        if (start) {
            this.setState({
                startOptions: options
            });
        } else {
            this.setState({
                endOptions: options
            });
        }
    }

    searchTime = () => {
        return [];
    };

    render() {
        const {startTime, endTime, startOptions, endOptions} = this.state;
        return (
            <div>
                <Dropdown options={startOptions}
                          search={(list, query) => this.searchTime(list, query)}
                          selection
                          allowAdditions
                          additionLabel=""
                          styleName="time-dropdown"
                          value={_serializeTime(startTime)}
                          onChange={(_, {value}) => {
                              this.setStartTime(value, endTime);
                          }} />
                <Dropdown options={endOptions}
                          search={(list, query) => this.searchTime(list, query, false)}
                          selection
                          allowAdditions
                          additionLabel=""
                          styleName="time-dropdown"
                          value={_serializeTime(endTime)}
                          onChange={(_, {value}) => {
                              this.setEndTime(startTime, value);
                          }} />
            </div>
        );
    }
}
