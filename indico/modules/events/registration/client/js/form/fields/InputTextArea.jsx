// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

const attributeMap = {
  numberOfRows: 'rows',
  numberOfColumns: 'cols',
};

export default function InputTextArea({htmlName, disabled, ...props}) {
  const inputProps = {};
  Object.entries(attributeMap).forEach(([prop, attr]) => {
    const val = props[prop];
    if (val !== null && val > 0) {
      inputProps[attr] = val;
    }
  });
  return <textarea name={htmlName} {...inputProps} disabled={disabled} />;
}

InputTextArea.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  numberOfRows: PropTypes.number,
  numberOfColumns: PropTypes.number,
};

InputTextArea.defaultProps = {
  disabled: false,
  numberOfRows: 2,
  numberOfColumns: 60,
};
