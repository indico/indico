// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

import {Translate} from 'indico/react/i18n';

/** Special value indicating that chained validation should stop immediately. */
const STOP_VALIDATION = Symbol('STOP_VALIDATION');

function number() {
  return value => {
    if (typeof value !== 'number' && (typeof value !== 'string' || Number.isNaN(+value))) {
      return Translate.string('Value must be a number');
    }
  };
}

function min(minValue) {
  return chain(number(), value => {
    const val = parseInt(value, 10);
    if (value !== '' && val < minValue) {
      return Translate.string('Value must be at least {minValue}', {minValue});
    }
  });
}

function max(maxValue) {
  return chain(number(), value => {
    const val = parseInt(value, 10);
    if (value !== '' && val > maxValue) {
      return Translate.string('Value must be at most {maxValue}', {maxValue});
    }
  });
}

function range(minValue, maxValue) {
  return chain(min(minValue), max(maxValue));
}

function minLength(length) {
  return value => {
    if (value.length < length) {
      return Translate.string('Value must be at least {length} chars', {length});
    }
  };
}

function maxLength(length) {
  return value => {
    if (value.length > length) {
      return Translate.string('Value must be at most {length} chars', {length});
    }
  };
}

function url(value) {
  if (!value.match(/https?:\/\/.+/)) {
    return Translate.string('Please provide a valid URL');
  }
}

function required(value) {
  const errorMsg = Translate.string('This field is required.');
  if (Array.isArray(value)) {
    return value.length !== 0 ? undefined : errorMsg;
  }
  return value || value === 0 ? undefined : errorMsg;
}

function optional(arg = null) {
  if (arg !== null) {
    // shortcut to allow `v.optional(v.something())`
    return chain(optional(), arg);
  }
  return value => {
    if (value === null || value === undefined) {
      return STOP_VALIDATION;
    }
  };
}

function chain(...validators) {
  return value => {
    for (const validator of validators) {
      const rv = validator(value);
      if (rv === STOP_VALIDATION) {
        break;
      } else if (rv) {
        // we got an error -> stop validating and return it
        return rv;
      }
    }
  };
}

/**
 * Succeeds if at least one validator succeeds,
 * otherwise returns the last error message.
 */
function or(...validators) {
  return value => {
    let rv;
    for (const validator of validators) {
      rv = validator(value);
      if (!rv || rv === STOP_VALIDATION) {
        // validator succeeded -> return
        return;
      }
    }
    return rv;
  };
}

function dates() {
  return value => {
    if (!value || !Object.values(value).every(x => x)) {
      return Translate.string('Please choose a valid period.');
    }
  };
}

/**
 * Validates that a datetime field contains a valid ISO 8601 value, optionally within bounds.
 * @param {moment.Moment} minStartDt - The earliest allowed date and time.
 * @param {moment.Moment} maxEndDt - The latest allowed date and time.
 */
function datetime(minStartDt = null, maxEndDt = null) {
  return value => {
    const dt = moment(value, moment.ISO_8601, true);
    if (!dt.isValid()) {
      return Translate.string('Please enter a valid date and time.');
    }
    if (minStartDt && dt.isBefore(minStartDt)) {
      return Translate.string('The entered date and time cannot be earlier than {min}.', {
        min: minStartDt.format('L LT'),
      });
    }
    if (maxEndDt && dt.isAfter(maxEndDt)) {
      return Translate.string('The entered date and time cannot be later than {max}.', {
        max: maxEndDt.format('L LT'),
      });
    }
  };
}

export default {
  number,
  min,
  max,
  range,
  minLength,
  maxLength,
  url,
  required,
  optional,
  chain,
  or,
  dates,
  datetime,
  STOP_VALIDATION,
};
