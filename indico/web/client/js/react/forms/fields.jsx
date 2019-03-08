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
import {Checkbox, Dropdown, Form, Popup, Radio} from 'semantic-ui-react';

import './ReduxFormField.module.scss';


export function ReduxFormField(
    {
        input, label, placeholder, required, children, disabled, componentLabel, defaultValue, fieldProps,
        hideValidationError,
        meta: {touched, error, submitError, submitting, dirty, dirtySinceLastSubmit},
        as: Component,
        ...props
    }
) {
    // we show errors if:
    // - the field was touched (focused+unfocused)
    //   ...and failed local validation
    //   ...and does not have the initial value
    // - there was an error during submission
    //   ...and the field has not been modified since the failed submission
    let errorMessage = null;
    if (touched && error && (dirty || required)) {
        if (!hideValidationError) {
            errorMessage = error;
        }
    } else if (submitError && !dirtySinceLastSubmit && !submitting) {
        errorMessage = submitError;
    }

    const field = (
        <Form.Field required={required} error={!!errorMessage} defaultValue={defaultValue} {...fieldProps}>
            {label && <label>{label}</label>}
            <Component {...input}
                       {...props}
                       label={componentLabel}
                       placeholder={placeholder}
                       required={required}
                       disabled={disabled || submitting} />
            {children}
        </Form.Field>
    );

    return (
        <Popup trigger={field}
               position="left center"
               open={!!errorMessage}>
            <div styleName="field-error">
                {errorMessage}
            </div>
        </Popup>
    );
}

ReduxFormField.propTypes = {
    disabled: PropTypes.bool,
    input: PropTypes.object.isRequired,
    required: PropTypes.bool,
    hideValidationError: PropTypes.bool,
    label: PropTypes.string,
    componentLabel: PropTypes.oneOfType([PropTypes.string, PropTypes.exact({children: PropTypes.node})]),
    placeholder: PropTypes.string,
    meta: PropTypes.object.isRequired,
    as: PropTypes.oneOfType([PropTypes.string, PropTypes.object, PropTypes.func]).isRequired,
    children: PropTypes.node,
    defaultValue: PropTypes.any,
    fieldProps: PropTypes.object,
};

ReduxFormField.defaultProps = {
    disabled: false,
    required: false,
    hideValidationError: false,
    placeholder: null,
    label: null,
    componentLabel: null,
    children: null,
    defaultValue: null,
    fieldProps: {},
};


export function ReduxRadioField({input, input: {value}, radioValue, ...props}) {
    return (
        <ReduxFormField input={input}
                        {...props}
                        as={Radio}
                        checked={radioValue === value}
                        onChange={(__, {checked}) => {
                            if (checked) {
                                input.onChange(radioValue);
                            }
                        }} />
    );
}

ReduxRadioField.propTypes = {
    input: PropTypes.object.isRequired,
    radioValue: PropTypes.string.isRequired
};


export function ReduxCheckboxField({input: {value, ...input}, ...props}) {
    return (
        <ReduxFormField input={input}
                        {...props}
                        checked={value === true}
                        as={Checkbox}
                        onChange={(__, {checked}) => {
                            input.onChange(checked);
                        }} />
    );
}

ReduxCheckboxField.propTypes = {
    input: PropTypes.object.isRequired,
};


export function ReduxDropdownField({input, required, clearable, onChange, ...props}) {
    return (
        <ReduxFormField input={input}
                        {...props}
                        required={required}
                        as={Dropdown}
                        clearable={clearable === undefined ? !required : clearable}
                        selectOnBlur={false}
                        onChange={(__, {value}) => {
                            input.onChange(value);
                            onChange(value);
                        }} />
    );
}


ReduxDropdownField.propTypes = {
    input: PropTypes.object.isRequired,
    required: PropTypes.bool,
    clearable: PropTypes.bool,
    onChange: PropTypes.func,
};

ReduxDropdownField.defaultProps = {
    required: false,
    clearable: false,
    onChange: () => {},
};
