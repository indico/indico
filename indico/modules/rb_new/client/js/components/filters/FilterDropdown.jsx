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
import {Button, Icon} from 'antd';
import propTypes from 'prop-types';

import FilterOptions from './FilterOptions';


export default class FilterDropdown extends React.Component {
    static propTypes = {
        title: propTypes.element.isRequired,
        form: propTypes.func.isRequired,
        displayValue: propTypes.func.isRequired,
        setGlobalState: propTypes.func.isRequired,
        initialValues: propTypes.object.isRequired
    }

    static getDerivedStateFromProps({initialValues, displayValue}, prevState) {
        return {
            ...prevState,
            fieldValues: initialValues,
            displayValue: displayValue(initialValues)
        };
    }

    constructor(props) {
        super(props);
        this.state = {
            isSet: false
        };

        this.setFieldValue = this.setFieldValue.bind(this);
        this.setDisplayValue = this.setDisplayValue.bind(this);
    }

    setFieldValue(field, value) {
        // Do incremental state updates, to avoid working
        // on an outdated state (consecutive calls)
        const newState = this.setState((prevState) => ({
            ...prevState,
            fieldValues: {
                ...prevState.fieldValues,
                [field]: value
            }
        }));
        this.setState(newState);
    }

    setDisplayValue(fieldValues) {
        const {displayValue} = this.props;
        this.setState({
            displayValue: displayValue(fieldValues),
            isSet: true
        });
    }

    render() {
        const {title, form, initialValues, setGlobalState} = this.props;
        const {displayValue, isSet, fieldValues} = this.state;
        const formRef = React.createRef();
        return (
            <FilterOptions title={form(formRef, this.setFieldValue)}
                           placement="bottomRight"
                           trigger={['click']}
                           onConfirm={() => {
                               this.setDisplayValue(fieldValues);
                               setGlobalState(fieldValues);
                           }}
                           onCancel={() => {
                               formRef.current.resetFields(initialValues);
                           }}>
                <Button type={isSet ? 'primary' : ''}>
                    {isSet ? displayValue : title}
                    <Icon type="down" />
                </Button>
            </FilterOptions>
        );
    }
}
