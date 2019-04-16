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
import {FORM_ERROR} from 'final-form';


function flatten(value) {
    // marshmallow's List returns an object with the index as the key
    if (_.isPlainObject(value)) {
        value = Object.values(value);
    }
    // Nested returns an object mapping the inner field name to its error(s)
    return _.uniq(_.flattenDeep(value.map(x => (_.isPlainObject(x) ? Object.values(x) : x))));
}

export function handleSubmissionError(error, defaultMessage = null, fieldErrorMap = {}) {
    const webargsErrors = _.get(error, 'response.data.webargs_errors');
    if (webargsErrors && error.response.status === 422) {
        if (Array.isArray(webargsErrors)) {
            // schema-level validation failed
            return {[FORM_ERROR]: webargsErrors.join(' / ')};
        }
        // flatten errors in case there's more than one
        return _.fromPairs(Object.entries(webargsErrors).map(([field, errors]) => {
            return [fieldErrorMap[field] || field, flatten(errors).join(' / ')];
        }));
    } else {
        return {[FORM_ERROR]: defaultMessage || error.message};
    }
}
