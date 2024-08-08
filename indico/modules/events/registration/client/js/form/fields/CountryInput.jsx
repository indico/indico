// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';

import {FinalCheckbox, FinalDropdown} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import '../../../styles/regform.module.scss';

import {getStaticData} from '../selectors';

const isoToFlag = country =>
  String.fromCodePoint(...country.split('').map(c => c.charCodeAt() + 0x1f1a5));

export default function CountryInput({htmlId, htmlName, disabled, isRequired, choices}) {
  return (
    <FinalDropdown
      id={htmlId}
      name={htmlName}
      required={isRequired}
      disabled={disabled}
      clearable={!isRequired}
      styleName="country-dropdown"
      placeholder={Translate.string('Select a country')}
      fluid
      selection
      options={choices.map(country => ({
        key: country.countryKey,
        value: country.countryKey,
        text: `${isoToFlag(country.countryKey)} ${country.caption}`,
      }))}
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
