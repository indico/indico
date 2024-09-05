// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import './Checkbox.module.scss';

export default function Checkbox({label, onChange, ...inputProps}) {
  // Type, whether specified or not, will always be 'checkbox'
  inputProps.type = 'checkbox';

  const handleChange = evt => {
    onChange(evt, {checked: evt.target.checked});
  };

  return (
    <label>
      <span styleName="checkbox-label">
        <input styleName="checkbox" onChange={handleChange} {...inputProps} />
        <span>{label}</span>
      </span>
    </label>
  );
}

Checkbox.propTypes = {
  label: PropTypes.oneOfType([PropTypes.string, PropTypes.element]).isRequired,
  onChange: PropTypes.func.isRequired,
};
