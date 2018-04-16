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
import propTypes from 'prop-types';

import {TimePicker} from 'antd';
import {toMoment} from '../../util';

const _serializeTime = time => (time ? time.format('HH:mm') : null);

export default class TimeForm extends React.Component {
    static propTypes = {
        startTime: propTypes.string,
        endTime: propTypes.string,
        setParentField: propTypes.func.isRequired
    }

    static defaultProps = {
        startTime: null,
        endTime: null
    }

    static getDerivedStateFromProps({startTime, endTime}, prevState) {
        // if there is no internal state, get the values from props
        return {
            ...prevState,
            startTime: prevState.startTime ? prevState.startTime : toMoment(startTime),
            endTime: prevState.endTime ? prevState.endTime : toMoment(endTime)
        };
    }

    constructor(props) {
        super(props);
        this.state = {};
    }

    resetFields({startTime, endTime}) {
        // version from parent/redux will be serialized
        this.setTimes(toMoment(startTime), toMoment(endTime));
    }

    setTimes(startTime, endTime) {
        const {setParentField} = this.props;

        // send serialized versions to parent/redux
        setParentField('startTime', _serializeTime(startTime));
        setParentField('endTime', _serializeTime(endTime));

        this.setState({
            startTime,
            endTime
        });
    }

    render() {
        const {startTime, endTime} = this.state;
        const props = {
            minuteStep: 15,
            format: 'HH:mm',
            getPopupContainer: trigger => trigger.parentNode
        };
        return (
            <div>
                <TimePicker value={startTime}
                            {...props}
                            onChange={(value) => {
                                this.setTimes(value, endTime);
                            }} />
                -
                <TimePicker value={endTime}
                            {...props}
                            onChange={(value) => {
                                this.setTimes(startTime, value);
                            }} />
            </div>
        );
    }
}
