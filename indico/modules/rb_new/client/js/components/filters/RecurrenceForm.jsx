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
import {Form, Input, Radio, Select} from 'semantic-ui-react';
import propTypes from 'prop-types';

import {Translate} from 'indico/react/i18n';

import FilterFormComponent from './FilterFormComponent';

import './RecurrenceForm.module.scss';


export default class RecurrenceForm extends FilterFormComponent {
    static propTypes = {
        type: propTypes.string,
        interval: propTypes.string,
        number: propTypes.number,
        ...FilterFormComponent.propTypes
    };

    static defaultProps = {
        type: null,
        interval: null,
        number: null
    }

    constructor(props) {
        super(props);
        this.onTypeChange = (e) => {
            this.stateChanger('type')(e.target.value);
        };
        this.onTypeChange = this.stateChanger('type');
        this.onNumberChange = this.stateChanger('number', (num) => Math.abs(parseInt(num, 10) || 1));
        this.onIntervalChange = this.stateChanger('interval');
    }

    stateChanger(param, sanitizer = (v => v)) {
        const {setParentField} = this.props;
        return (_, {value}) => {
            value = sanitizer(value);
            // update both internal state (for rendering purposes and that of the parent)
            setParentField(param, value);
            this.setState({
                [param]: value
            });
        };
    }

    render() {
        const {type, interval, number} = this.state;
        const intervalOptions = [
            {
                value: 'day',
                text: Translate.string('Days')
            },
            {
                value: 'week',
                text: Translate.string('Weeks')
            },
            {
                value: 'month',
                text: Translate.string('Months')
            }
        ];

        return (
            <Form>
                <Form.Field>
                    <Radio value="single"
                           name="type"
                           checked={type === 'single'}
                           label={Translate.string('Single booking')}
                           onChange={this.onTypeChange} />
                </Form.Field>
                <Form.Field>
                    <Radio value="daily"
                           name="type"
                           checked={type === 'daily'}
                           label={Translate.string('Daily')}
                           onChange={this.onTypeChange} />
                </Form.Field>
                <Form.Group inline styleName="recurrence-every">
                    <Form.Field>
                        <Radio value="every"
                               name="type"
                               checked={type === 'every'}
                               label={Translate.string('Every')}
                               onChange={this.onTypeChange} />
                    </Form.Field>
                    <Form.Field>
                        <Input value={number}
                               type="number"
                               min="1"
                               max="99"
                               disabled={type !== 'every'}
                               onChange={this.onNumberChange} />
                    </Form.Field>
                    <Form.Field>
                        <Select value={interval}
                                disabled={type !== 'every'}
                                onChange={this.onIntervalChange}
                                options={intervalOptions} />
                    </Form.Field>
                </Form.Group>
            </Form>
        );
    }
}
