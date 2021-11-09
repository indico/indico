// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {mapPropsToAttributes} from './util';

const attributeMap = {length: 'size', minLength: 'minLength', maxLength: 'maxLength'};

export default function InputText({htmlName, disabled, ...props}) {
  const inputProps = mapPropsToAttributes(props, attributeMap);
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
