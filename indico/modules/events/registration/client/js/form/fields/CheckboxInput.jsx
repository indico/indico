// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import '../../../styles/regform.module.scss';

export default function CheckboxInput({htmlName, disabled, title, isRequired}) {
  return (
    <label styleName="checkbox-input-label">
      <input type="checkbox" name={htmlName} disabled={disabled} />
      {title}
      {isRequired && <span styleName="required">*</span>}
    </label>
  );
}

CheckboxInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  title: PropTypes.string.isRequired,
  isRequired: PropTypes.bool.isRequired,
};

CheckboxInput.defaultProps = {
  disabled: false,
};
