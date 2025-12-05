// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {FinalCheckbox, FinalInput} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import '../../../styles/regform.module.scss';

export default function PhoneInput({
  htmlId,
  htmlName,
  isRequired,
  disabled,
  requireInternationalFormat,
}) {
  const validateInternationalPhone = value => {
    if (!value || !requireInternationalFormat) return undefined;

    // Check if the phone number starts with + followed by digits
    const internationalPhonePattern = /^\+[1-9]\d{1,14}$/;

    if (!internationalPhonePattern.test(value.replace(/[\s()-]/g, ''))) {
      return 'Please enter a valid phone number with international prefix (e.g., +41 22 123 4567)';
    }
    return undefined;
  };

  return (
    <FinalInput
      id={htmlId}
      type="tel"
      name={htmlName}
      required={isRequired}
      disabled={disabled}
      validate={validateInternationalPhone}
    />
  );
}

export function PhoneSettings() {
  return (
    <FinalCheckbox
      name="requireInternationalFormat"
      label={Translate.string('Require international format (e.g., +41 22 123 4567)')}
    />
  );
}

PhoneInput.propTypes = {
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  isRequired: PropTypes.bool.isRequired,
  disabled: PropTypes.bool,
  requireInternationalFormat: PropTypes.bool,
};

PhoneInput.defaultProps = {
  disabled: false,
  requireInternationalFormat: false,
};
