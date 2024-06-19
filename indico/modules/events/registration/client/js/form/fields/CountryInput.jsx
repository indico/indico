// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';
import {Dropdown} from 'semantic-ui-react';

import {FinalCheckbox, FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import '../../../styles/regform.module.scss';

import {getStaticData} from '../selectors';

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
      selectOnBlur={false}
      selectOnNavigation={false}
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

export default function CountryInput({htmlId, htmlName, disabled, isRequired, choices}) {
  return (
    <FinalField
      id={htmlId}
      name={htmlName}
      component={CountryInputComponent}
      required={isRequired}
      disabled={disabled}
      choices={choices}
      clearable={!isRequired}
      parse={x => x}
    />
  );
}

CountryInput.propTypes = {
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  choices: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
};

CountryInput.defaultProps = {
  disabled: false,
  isRequired: false,
};

export function CountrySettings({htmlName}) {
  const {hasPredefinedAffiliations} = useSelector(getStaticData);
  if (htmlName !== 'country' || !hasPredefinedAffiliations) {
    return null;
  }
  return (
    <FinalCheckbox
      name="useAffiliationCountry"
      label={Translate.string('Default to affiliation country')}
    />
  );
}

CountrySettings.propTypes = {
  htmlName: PropTypes.string,
};

CountrySettings.defaultProps = {
  htmlName: undefined,
};
