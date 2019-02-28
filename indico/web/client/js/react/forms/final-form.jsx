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

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {Field} from 'react-final-form';


export function getChangedValues(data, form) {
    const fields = form.getRegisteredFields().filter(x => !x.includes('['));
    return _.fromPairs(fields.filter(name => form.getFieldState(name).dirty).map(name => [name, data[name]]));
}

/** Conditionally show content within a FinalForm depending on the value of another field */
export const FieldCondition = ({when, is, children}) => (
    <Field name={when}
           subscription={{value: true}}
           render={({input: {value}}) => (value === is ? children : null)} />
);

FieldCondition.propTypes = {
    when: PropTypes.string.isRequired,
    is: PropTypes.any,
    children: PropTypes.node.isRequired,
};

FieldCondition.defaultProps = {
    is: true,
};
