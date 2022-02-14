// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';
import {Dropdown} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import '../../../styles/regform.module.scss';

const isoToFlag = country =>
  String.fromCodePoint(...country.split('').map(c => c.charCodeAt() + 0x1f1a5));

function CountryInputComponent({value, onChange, disabled, choices, clearable}) {
  return (
    <Dropdown
      styleName="country-dropdown"
      placeholder={Translate.string('Select a country')}
      fluid
      search
      selection
      disabled={disabled}
      clearable={clearable}
      value={value}
      onChange={(_, {value: newValue = ''}) => onChange(newValue)}
      options={choices.map(country => ({
        key: country.countryKey,
        value: country.countryKey,
        text: `${isoToFlag(country.countryKey)} ${country.caption}`,
      }))}
    />
  );
}

CountryInputComponent.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
  choices: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
  clearable: PropTypes.bool.isRequired,
};

export default function CountryInput({htmlName, disabled, isRequired, defaultValue, choices}) {
  const setupMode = useSelector(state => !!state.staticData.setupMode);
  return (
    <FinalField
      name={htmlName}
      component={CountryInputComponent}
      required={isRequired}
      disabled={disabled}
      defaultValue={setupMode ? defaultValue : undefined}
      choices={choices}
      clearable={!isRequired}
      parse={x => x}
    />
  );
}

CountryInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  defaultValue: PropTypes.string.isRequired,
  choices: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
};

CountryInput.defaultProps = {
  disabled: false,
  isRequired: false,
};
