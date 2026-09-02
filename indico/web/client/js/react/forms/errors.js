// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {FORM_ERROR} from 'final-form';
import _ from 'lodash';

function flatten(value, joinErrors, preserveNested) {
  if (preserveNested) {
    // When using a nested schema that's populated by individual final-form fields (ie field names
    // whose name contains a dot, e.g. `custom_fields.custom_123`), we want to preserve this
    // structure in order to show errors on the actual fields.
    // XXX this only supports one level of nesting, ie not `foo.bar.baz` etc
    return Object.fromEntries(
      Object.entries(value).map(([field, errors]) => {
        return [field, joinErrors ? errors.join(' / ') : errors];
      })
    );
  }
  // marshmallow's List returns an object with the index as the key
  if (_.isPlainObject(value)) {
    value = Object.values(value);
  }
  // Nested returns an object mapping the inner field name to its error(s)
  const res = _.uniq(_.flattenDeep(value.map(x => (_.isPlainObject(x) ? Object.values(x) : x))));
  return joinErrors ? res.join(' / ') : res;
}

/**
 * Handle an error during a form submission.
 *
 * This is an internal util; if you are looking for a function to handle any error
 * that could happen from a form submission request (including unexpected errors),
 * use the `handleSubmitError` function instead (which will call this function if
 * appropriate but also take care of showing an error report dialog otherwise).
 */
export function handleSubmissionError(
  error,
  defaultMessage = null,
  fieldErrorMap = {},
  joinErrors = true,
  preserveNested = []
) {
  const webargsErrors = _.get(error, 'response.data.webargs_errors');
  if (webargsErrors && error.response.status === 422) {
    if (Array.isArray(webargsErrors)) {
      // schema-level validation failed
      return {[FORM_ERROR]: joinErrors ? webargsErrors.join(' / ') : webargsErrors};
    }
    // flatten errors in case there's more than one
    return Object.fromEntries(
      Object.entries(webargsErrors).map(([field, errors]) => {
        return [
          fieldErrorMap[field] || field,
          flatten(errors, joinErrors, preserveNested.includes(field)),
        ];
      })
    );
  } else {
    const message = defaultMessage || error.response?.data?.error?.message || error.message;
    return {[FORM_ERROR]: joinErrors ? message : [message]};
  }
}
