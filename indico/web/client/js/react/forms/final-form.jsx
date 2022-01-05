// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {FORM_ERROR} from 'final-form';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Field} from 'react-final-form';

import {handleAxiosError} from '../../utils/axios';

import {handleSubmissionError} from './errors';

export function getChangedValues(data, form) {
  const fields = form.getRegisteredFields().filter(x => !x.includes('['));
  return _.fromPairs(
    fields.filter(name => form.getFieldState(name).dirty).map(name => [name, data[name]])
  );
}

/**
 * Handle the error from an axios request, taking into account submission
 * errors that can be handled by final-form instead of showing the usual
 * error dialog for them.
 */
export function handleSubmitError(error, fieldErrorMap = {}) {
  if (_.get(error, 'response.status') === 422) {
    // if it's 422 we assume it's from webargs validation
    return handleSubmissionError(error, null, fieldErrorMap);
  } else if (_.get(error, 'response.status') === 418) {
    // this is an error that was expected, and will be handled by the app
    return {[FORM_ERROR]: error.response.data.message};
  } else {
    // anything else here is unexpected and triggers the usual error dialog
    const message = handleAxiosError(error, true);
    return {[FORM_ERROR]: message};
  }
}

/** Conditionally show content within a FinalForm depending on the value of another field */
export const FieldCondition = ({when, is, children}) => (
  <Field
    name={when}
    subscription={{value: true}}
    render={({input: {value}}) => (value === is ? children : null)}
  />
);

FieldCondition.propTypes = {
  when: PropTypes.string.isRequired,
  is: PropTypes.any,
  children: PropTypes.node.isRequired,
};

FieldCondition.defaultProps = {
  is: true,
};
