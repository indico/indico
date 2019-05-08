// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

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
