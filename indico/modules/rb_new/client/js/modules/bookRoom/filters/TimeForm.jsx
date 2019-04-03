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

import {serializeTime, toMoment} from 'indico/utils/date';
import {FilterFormComponent} from '../../../common/filters';
import TimeRangePicker from '../../../components/TimeRangePicker';

import './TimeForm.module.scss';


export default class TimeForm extends FilterFormComponent {
    static propTypes = {
        startTime: PropTypes.string,
        endTime: PropTypes.string,
        allowPastTimes: PropTypes.bool.isRequired,
        ...FilterFormComponent.propTypes
    };

    static defaultProps = {
        startTime: null,
        endTime: null
    };

    static getDerivedStateFromProps({startTime, endTime}, prevState) {
        // if there is no internal state, get the values from props
        return {
            startTime: toMoment(startTime, 'HH:mm'),
            endTime: toMoment(endTime, 'HH:mm'),
            ...prevState
        };
    }

    constructor(props) {
        super(props);
        this.formRef = React.createRef();
    }

    setTimes = async (startTime, endTime) => {
        const {setParentField} = this.props;
        const {startTime: prevStartTime, endTime: prevEndTime} = this.state;

        // if everything stays the same, do nothing
        if (startTime === prevStartTime && endTime === prevEndTime) {
            return;
        }

        // send serialized versions to parent/redux
        await setParentField('startTime', serializeTime(startTime));
        await setParentField('endTime', serializeTime(endTime));

        this.setState({
            startTime,
            endTime
        });
    };

    render() {
        const {startTime, endTime} = this.state;
        const {allowPastTimes} = this.props;
        return (
            <div ref={this.formRef}>
                <TimeRangePicker startTime={startTime}
                                 endTime={endTime}
                                 onChange={this.setTimes}
                                 allowPastTimes={allowPastTimes} />
            </div>
        );
    }
}
