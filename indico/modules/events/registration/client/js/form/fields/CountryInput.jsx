// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Dropdown} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import styles from '../../../styles/regform.module.scss';

const isoToFlag = country =>
  String.fromCodePoint(...country.split('').map(c => c.charCodeAt() + 0x1f1a5));

function CountryInputComponent({value, onChange, disabled, choices}) {
  return (
    <Dropdown
      styleName="country-dropdown"
      placeholder={Translate.string('Select a country')}
      fluid
      search
      selection
      disabled={disabled}
      value={value}
      onChange={(_, {value: newValue}) => onChange(newValue)}
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
};

export default function CountryInput({htmlName, disabled, isRequired, defaultValue, choices}) {
  return (
    <FinalField
      name={htmlName}
      component={CountryInputComponent}
      required={isRequired}
      disabled={disabled}
      fieldProps={{className: styles.field}}
      defaultValue={defaultValue}
      choices={choices}
    />
  );
}

CountryInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  defaultValue: PropTypes.string,
  choices: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
};

CountryInput.defaultProps = {
  disabled: false,
  isRequired: false,
  defaultValue: '',
};
