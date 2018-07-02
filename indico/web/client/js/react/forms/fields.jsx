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
import {Form, Label} from 'semantic-ui-react';


export function ReduxFormField(
    {
        input, label, placeholder, required, children, disabled, componentLabel,
        meta: {touched, error, submitError, disabled: metaDisabled, submitting, dirty, dirtySinceLastSubmit},
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
    let errorLabel = null;
    if (touched && error && dirty) {
        errorLabel = <Label basic color="red" pointing="above" content={error} />;
    } else if (submitError && !dirtySinceLastSubmit) {
        errorLabel = <Label basic color="red" pointing="above" content={submitError} />;
    }
    return (
        <Form.Field required={required} error={!!errorLabel}>
            {label && <label>{label}</label>}
            <Component {...input}
                       {...props}
                       label={componentLabel}
                       placeholder={placeholder}
                       disabled={disabled || metaDisabled || submitting} />
            {errorLabel}
            {children}
        </Form.Field>
    );
}

ReduxFormField.propTypes = {
    disabled: PropTypes.bool,
    input: PropTypes.object.isRequired,
    required: PropTypes.bool,
    label: PropTypes.string,
    componentLabel: PropTypes.string,
    placeholder: PropTypes.string,
    meta: PropTypes.object.isRequired,
    as: PropTypes.oneOfType([PropTypes.string, PropTypes.object, PropTypes.func]).isRequired,
    children: PropTypes.node,
};

ReduxFormField.defaultProps = {
    disabled: false,
    required: false,
    placeholder: null,
    label: null,
    componentLabel: null,
    children: null,
};

export function ReduxRadioField({input, input: {value}, radioValue, ...props}) {
    return (
        <ReduxFormField input={input}
                        {...props}
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
