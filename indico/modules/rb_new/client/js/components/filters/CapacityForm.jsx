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

import {Button, InputNumber} from 'antd';

import FilterFormComponent from './FilterFormComponent';


export default class CapacityForm extends FilterFormComponent {
    setCapacity(capacity) {
        const {setParentField} = this.props;

        setParentField('capacity', capacity);
        this.setState({
            capacity
        });
    }

    render() {
        const {capacity} = this.state;
        return (
            <div>
                <InputNumber min={1}
                             value={capacity}
                             step={10}
                             onChange={value => {
                                 this.setCapacity(value);
                             }} />
                <Button shape="circle"
                        icon="close"
                        type="dashed"
                        disabled={!capacity}
                        onClick={() => {
                            this.setCapacity(null);
                        }} />
            </div>
        );
    }
}
