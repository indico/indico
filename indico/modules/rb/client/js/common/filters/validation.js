// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {push} from 'connected-react-router';

import showReactErrorDialog from 'indico/react/errors';
import {Translate} from 'indico/react/i18n';
import {toMoment} from 'indico/utils/date';

import {resetPageState} from '../../actions';

/**
 * Performs more complex validation of the filter parameters, combining more than one value.
 * @param {Object} filters - Filters to validate.
 * @returns {boolean} Whether it's valid or not.
 */
const mixedValidator = filters => {
  if (!('timeSlot' in filters)) {
    return true;
  }

  const {
    timeSlot: {startTime: st, endTime: et},
  } = filters;
  return !(st && et && toMoment(st, 'HH:mm').isSameOrAfter(toMoment(et, 'HH:mm')));
};

/**
 * @param {Object} filters - Filters to validate.
 * @param namespace
 * @param dispatch
 * @returns {boolean} Whether it's valid or not.
 */
export const validateFilters = (filters, namespace, dispatch) => {
  if (!filters.error && mixedValidator(filters)) {
    return true;
  }
  const error = {
    title: Translate.string('Something went wrong'),
    message: Translate.string('The provided URL was not properly formatted.'),
  };
  dispatch(resetPageState(namespace));
  dispatch(push('/'));
  showReactErrorDialog(error);
  return false;
};
