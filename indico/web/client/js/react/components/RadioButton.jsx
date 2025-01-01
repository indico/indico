// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import './RadioButton.module.scss';

export default function RadioButton({label, ...inputProps}) {
  return (
    <label styleName="radio-label">
      <input {...inputProps} type="radio" styleName="radio" />
      <span>{label}</span>
    </label>
  );
}

RadioButton.propTypes = {
  label: PropTypes.oneOfType([PropTypes.string, PropTypes.element]).isRequired,
};
