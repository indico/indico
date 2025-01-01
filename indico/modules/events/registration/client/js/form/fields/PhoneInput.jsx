// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {FinalInput} from 'indico/react/forms';

import '../../../styles/regform.module.scss';

export default function PhoneInput({htmlId, htmlName, isRequired, disabled}) {
  return (
    <FinalInput id={htmlId} type="tel" name={htmlName} required={isRequired} disabled={disabled} />
  );
}

PhoneInput.propTypes = {
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  isRequired: PropTypes.bool.isRequired,
  disabled: PropTypes.bool,
};

PhoneInput.defaultProps = {
  disabled: false,
};
