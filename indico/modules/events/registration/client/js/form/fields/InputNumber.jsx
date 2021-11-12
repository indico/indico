// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {FinalInput, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

export default function InputNumber({htmlName, disabled, minValue}) {
  return <input type="number" name={htmlName} disabled={disabled} min={minValue} />;
}

InputNumber.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  minValue: PropTypes.number,
};

InputNumber.defaultProps = {
  disabled: false,
  minValue: 0,
};

export function NumberSettings() {
  return (
    <FinalInput
      name="minValue"
      type="number"
      label={Translate.string('Minimum')}
      placeholder={String(InputNumber.defaultProps.minValue)}
      step="1"
      min="0"
      validate={v.optional(v.min(0))}
    />
  );
}
