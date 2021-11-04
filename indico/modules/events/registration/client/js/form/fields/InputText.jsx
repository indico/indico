// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

const attributeMap = {length: 'size', minLength: 'minLength', maxLength: 'maxLength'};

export default function InputText({htmlName, disabled, ...props}) {
  const inputProps = {};
  Object.entries(attributeMap).forEach(([prop, attr]) => {
    const val = props[prop];
    if (val !== null && val > 0) {
      inputProps[attr] = val;
    }
  });
  return <input type="text" name={htmlName} {...inputProps} disabled={disabled} />;
}

InputText.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  length: PropTypes.number,
  minLength: PropTypes.number,
  maxLength: PropTypes.number,
};

InputText.defaultProps = {
  disabled: false,
  length: null,
  minLength: null,
  maxLength: null,
};
