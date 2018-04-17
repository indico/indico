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


function _mergeDefaults(defaults, values) {
    return Object.assign(...Object.entries(values).map(([key, value]) => {
        if (value === null && defaults[key] !== undefined) {
            return [key, defaults[key]];
        }
        return [key, value];
    }).map(([k, v]) => ({[k]: v})));
}

export default class FilterDropdown extends React.Component {
    static propTypes = {
        title: propTypes.element.isRequired,
        form: propTypes.func.isRequired,
        renderValue: propTypes.func.isRequired,
        setGlobalState: propTypes.func.isRequired,
        initialValues: propTypes.object,
        defaults: propTypes.object
    }

    static defaultProps = {
        initialValues: {},
        defaults: {}
    }

    static getDerivedStateFromProps({defaults, initialValues, renderValue}, prevState) {
        return {
            ...prevState,
            fieldValues: _mergeDefaults(defaults, initialValues),
            renderedValue: renderValue(initialValues)
        };
    }

    constructor(props) {
        super(props);
        this.state = {};

        this.setFieldValue = this.setFieldValue.bind(this);
        this.resetFields = this.resetFields.bind(this);
        this.setRenderedValue = this.setRenderedValue.bind(this);
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

    resetFields() {
        const {fieldValues} = this.state;
        Object.keys(fieldValues).forEach(field => {
            this.setFieldValue(field, null);
        });
    }

    setRenderedValue(fieldValues) {
        const {renderValue} = this.props;
        const renderedValue = renderValue(fieldValues);
        this.setState({
            renderedValue,
        });
    }

    render() {
        const {title, form, defaults, initialValues, setGlobalState} = this.props;
        const {renderedValue, fieldValues} = this.state;
        const formRef = React.createRef();

        return (
            <FilterOptions title={form(formRef, fieldValues, this.setFieldValue, this.resetFields)}
                           placement="bottomRight"
                           trigger={['click']}
                           onConfirm={() => {
                               this.setRenderedValue(fieldValues);
                               setGlobalState(fieldValues);
                           }}
                           onCancel={() => {
                               formRef.current.resetFields(_mergeDefaults(defaults, initialValues));
                           }}>
                <Button type={renderedValue !== null ? 'primary' : ''}>
                    {renderedValue === null ? title : renderedValue}
                    <Icon type="down" />
                </Button>
            </FilterOptions>
        );
    }
}
