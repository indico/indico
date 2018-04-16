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
import {InputNumber, Radio, Select} from 'antd';
import propTypes from 'prop-types';

import {Translate} from 'indico/react/i18n';

import './RecurrenceForm.module.scss';


export default class RecurrenceForm extends React.Component {
    static propTypes = {
        type: propTypes.string.isRequired,
        interval: propTypes.string.isRequired,
        number: propTypes.number.isRequired,
        setParentField: propTypes.func.isRequired
    };

    constructor(props) {
        super(props);
        const {type, interval, number} = props;
        this.state = {type, interval, number};
        this.onTypeChange = (e) => {
            this.stateChanger('type')(e.target.value);
        };
        this.onNumberChange = this.stateChanger('number');
        this.onIntervalChange = this.stateChanger('interval');
    }

    resetFields(fields) {
        Object.entries(fields).forEach(([key, value]) => {
            this.stateChanger(key)(value);
        });
    }

    stateChanger(param) {
        const {setParentField} = this.props;
        return (value) => {
            // update both internal state (for rendering purposes and that of the parent)
            setParentField(param, value);
            this.setState({
                [param]: value
            });
        };
    }

    render() {
        const {type, interval, number} = this.state;
        return (
            <div>
                <Radio.Group value={type} onChange={this.onTypeChange}>
                    <Radio value="single" styleName="recurrence-freq-item">
                        <Translate>Single booking</Translate>
                    </Radio>
                    <Radio value="daily" styleName="recurrence-freq-item">
                        <Translate>Daily</Translate>
                    </Radio>
                    <div>
                        <Radio value="every">
                            <Translate>Every</Translate>
                        </Radio>
                        <InputNumber min={1}
                                     max={50}
                                     value={number}
                                     disabled={type !== 'every'}
                                     onChange={this.onNumberChange} />
                        <Select value={interval}
                                disabled={type !== 'every'}
                                getPopupContainer={trigger => trigger.parentNode}
                                onChange={this.onIntervalChange}>
                            <Select.Option value="day">
                                <Translate>Days</Translate>
                            </Select.Option>
                            <Select.Option value="week">
                                <Translate>Weeks</Translate>
                            </Select.Option>
                            <Select.Option value="month">
                                <Translate>Months</Translate>
                            </Select.Option>
                        </Select>
                    </div>
                </Radio.Group>
            </div>
        );
    }
}
