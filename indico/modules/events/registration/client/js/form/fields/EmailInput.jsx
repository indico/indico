// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {FinalInput} from 'indico/react/forms';

import '../../../styles/regform.module.scss';

export default function EmailInput({htmlName, disabled, isRequired}) {
  return <FinalInput type="email" name={htmlName} required={isRequired} disabled={disabled} />;
}

EmailInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool.isRequired,
};

EmailInput.defaultProps = {
  disabled: false,
};
