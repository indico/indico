// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import '../../../styles/regform.module.scss';

export default function EmailInput({htmlName, disabled}) {
  return <input type="email" name={htmlName} disabled={disabled} size="60" />;
}

EmailInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
};

EmailInput.defaultProps = {
  disabled: false,
};
