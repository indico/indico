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

import {Translate} from 'indico/react/i18n';


// TODO: move the stuff in here somewhere else

export function ReduxFormField(
    {
        input, label, placeholder, required, children,
        meta: {touched, invalid, error, disabled, submitting},
        as: Component,
        ...props
    }
) {
    return (
        <Form.Field required={required} error={touched && invalid}>
            {label && <label>{label}</label>}
            <Component {...input}
                       {...props}
                       placeholder={placeholder}
                       disabled={disabled || submitting} />
            {touched && error && <Label basic color="red" pointing="above" content={error} />}
            {children}
        </Form.Field>
    );
}

ReduxFormField.propTypes = {
    input: PropTypes.object.isRequired,
    required: PropTypes.bool,
    label: PropTypes.string,
    placeholder: PropTypes.string,
    meta: PropTypes.object.isRequired,
    as: PropTypes.oneOfType([PropTypes.string, PropTypes.object, PropTypes.func]).isRequired,
    children: PropTypes.node,
};

ReduxFormField.defaultProps = {
    required: false,
    placeholder: null,
    label: null,
    children: null,
};


export function fieldRequired(value) {
    return value ? undefined : Translate.string('This field is required.');
}
