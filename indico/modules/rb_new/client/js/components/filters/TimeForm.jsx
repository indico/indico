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
import TimePicker from 'rc-time-picker';
import 'rc-time-picker/assets/index.css';

import {toMoment} from '../../util';

import FilterFormComponent from './FilterFormComponent';
import './TimeForm.module.scss';


const _serializeTime = time => (time ? time.format('HH:mm') : null);

export default class TimeForm extends FilterFormComponent {
    static propTypes = {
        startTime: propTypes.string,
        endTime: propTypes.string,
        ...FilterFormComponent.propTypes
    }

    static defaultProps = {
        startTime: null,
        endTime: null
    }

    static getDerivedStateFromProps({startTime, endTime}, prevState) {
        // if there is no internal state, get the values from props
        return {
            ...prevState,
            startTime: toMoment(startTime, 'HH:mm'),
            endTime: toMoment(endTime, 'HH:mm')
        };
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
            minuteStep: 5,
            format: 'HH:mm',
            allowEmpty: false,
            showSecond: false,
            getPopupContainer: trigger => trigger.parentNode
        };
        return (
            <div>
                <TimePicker value={startTime}
                            styleName="time-picker"
                            {...props}
                            onChange={(value) => {
                                this.setTimes(value, endTime);
                            }} />
                -
                <TimePicker value={endTime}
                            styleName="time-picker"
                            {...props}
                            onChange={(value) => {
                                this.setTimes(startTime, value);
                            }} />
            </div>
        );
    }
}
