// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';

import {FinalDropdown} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getCurrency} from '../../form_setup/selectors';

export default function BooleanInput({htmlName, disabled, isRequired, defaultValue, price}) {
  const currency = useSelector(getCurrency);

  return (
    <select name={htmlName} disabled={disabled} defaultValue={defaultValue}>
      {!isRequired && <option value="">{Translate.string('Choose an option')}</option>}
      <option value="yes">
        {Translate.string('Yes')} {price && `(${price} ${currency})`}
      </option>
      <option value="no">{Translate.string('No')}</option>
    </select>
  );
}

BooleanInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  defaultValue: PropTypes.string,
  price: PropTypes.number,
};

BooleanInput.defaultProps = {
  disabled: false,
  isRequired: false,
  defaultValue: '',
  price: 0,
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
