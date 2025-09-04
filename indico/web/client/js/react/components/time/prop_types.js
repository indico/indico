// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';

import {DEFAULT_STEP_SIZE} from './shared';

const TIME_PATTERN = /^(?:[01]?\d|2[0-3]):[0-5]\d$/;

export function timeString(props, propName, componentName) {
  const value = props[propName];

  if (!value) {
    return;
  }

  if (!TIME_PATTERN.test(value)) {
    return new Error(
      `Invalid prop \`${propName}\` supplied to \`${componentName}\`. Expected format 'H:MM' or 'HH:MM'. Got '${value}'.`
    );
  }
}

// If you want it to be required:
timeString.isRequired = function(props, propName, componentName) {
  if (!props[propName]) {
    return new Error(
      `The prop \`${propName}\` is marked as required in \`${componentName}\`, but its value is \`${props[propName]}\`.`
    );
  }
  return timeString(props, propName, componentName);
};

export const commonProps = {
  onChange: PropTypes.func,
  step: PropTypes.number, // minutes
  min: timeString,
  max: timeString,
  timeFormat: PropTypes.oneOf(['24h', '12h']),
};

export const commonDefaults = {
  onChange: undefined,
  step: DEFAULT_STEP_SIZE,
  min: '0:00',
  max: '23:59',
  timeFormat: '24h',
};
