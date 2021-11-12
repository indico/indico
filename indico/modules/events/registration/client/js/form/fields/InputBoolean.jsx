// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {FinalDropdown} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

export default function InputBoolean({htmlName, disabled, isRequired, defaultValue}) {
  return (
    <select name={htmlName} disabled={disabled} defaultValue={defaultValue}>
      {!isRequired && <option value="">{Translate.string('Choose an option')}</option>}
      <option value="yes">{Translate.string('Yes')}</option>
      <option value="no">{Translate.string('No')}</option>
    </select>
  );
}

InputBoolean.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  defaultValue: PropTypes.string,
};

InputBoolean.defaultProps = {
  disabled: false,
  isRequired: false,
  defaultValue: '',
};

export function BooleanSettings() {
  const options = [
    {key: 'yes', value: 'yes', text: Translate.string('Yes')},
    {key: 'no', value: 'no', text: Translate.string('No')},
  ];
  return (
    <FinalDropdown
      name="defaultValue"
      label={Translate.string('Default value')}
      options={options}
      placeholder={Translate.string('None')}
      selection
    />
  );
}
