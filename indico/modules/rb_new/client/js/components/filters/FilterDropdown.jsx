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
import {Button, Icon, Popup} from 'semantic-ui-react';
import propTypes from 'prop-types';

import {Translate} from 'indico/react/i18n';

import './FilterDropdown.module.scss';


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
        defaults: propTypes.object,
        showButtons: propTypes.bool
    };

    static defaultProps = {
        initialValues: {},
        defaults: {},
        showButtons: true
    };

    static getDerivedStateFromProps({defaults, initialValues, renderValue}, prevState) {
        return {
            ...prevState,
            fieldValues: _mergeDefaults(defaults, initialValues),
            renderedValue: renderValue(initialValues)
        };
    }

    constructor(props) {
        super(props);
        this.state = {
            isOpen: false
        };

        this.setFieldValue = this.setFieldValue.bind(this);
        this.setRenderedValue = this.setRenderedValue.bind(this);
        this.handleOpen = this.handleOpen.bind(this);
        this.handleClose = this.handleClose.bind(this);
        this.handleOK = this.handleOK.bind(this);
        this.handleCancel = this.handleCancel.bind(this);
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

    resetFields(fieldValues) {
        this.setState({
            fieldValues
        });
    }

    setRenderedValue(fieldValues) {
        const {renderValue} = this.props;
        const renderedValue = renderValue(fieldValues);
        this.setState({
            renderedValue,
        });
    }

    handleClose() {
        this.setState({
            isOpen: false
        });
    }

    handleOpen() {
        this.setState({
            isOpen: true
        });
    }

    handleCancel() {
        const {defaults, initialValues} = this.props;
        this.resetFields(_mergeDefaults(defaults, initialValues));
        this.handleClose();
    }

    handleOK() {
        const {setGlobalState} = this.props;
        const {fieldValues} = this.state;
        this.setRenderedValue(fieldValues);
        setGlobalState(fieldValues);
        this.handleClose();
    }

    render() {
        const formRef = React.createRef();
        const {title, form, showButtons} = this.props;
        const {renderedValue, fieldValues, isOpen} = this.state;
        const trigger = (
            <Button primary={renderedValue !== null} styleName="filter-dropdown-button">
                {renderedValue === null ? title : renderedValue}
                <Icon name="angle down" />
            </Button>
        );

        return (
            <Popup position="bottom right"
                   trigger={trigger}
                   on="click"
                   open={isOpen}
                   onClose={this.handleClose}
                   onOpen={this.handleOpen}>
                {form(formRef, fieldValues, this.setFieldValue, this.handleOK)}
                {showButtons && (
                    <Button.Group size="mini" compact floated="right" styleName="filter-dropdown-footer">
                        <Button onClick={this.handleCancel}>
                            <Translate>Cancel</Translate>
                        </Button>
                        <Button positive onClick={this.handleOK}>
                            <Translate>OK</Translate>
                        </Button>
                    </Button.Group>
                )}
            </Popup>
        );
    }
}
