// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useMemo} from 'react';
import {useSelector} from 'react-redux';

import Select from 'indico/react/components/Select';
import {FinalCheckbox, FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getStaticData} from '../selectors';

const isoToFlag = country =>
  String.fromCodePoint(...country.split('').map(c => c.charCodeAt() + 0x1f1a5));

function CountryInputComponent({value, onChange, choices, ...inputProps}) {
  const [options, countryNameToKey, countryKeyToName] = useMemo(() => {
    const _options = [];
    const _countryNameToKey = new Map();
    const _countryKeyToName = new Map();
    choices.forEach(country => {
      _options.push([country.caption, `${isoToFlag(country.countryKey)} ${country.caption}`]);
      _countryNameToKey.set(country.caption, country.countryKey);
      _countryKeyToName.set(country.countryKey, country.caption);
    });
    return [_options, _countryNameToKey, _countryKeyToName];
  }, [choices]);

  const handleChange = ev => {
    onChange(countryNameToKey.get(ev.target.value) || ev.target.value);
  };

  return (
    <Select
      options={options}
      value={countryKeyToName.get(value) || value}
      onChange={handleChange}
      data-input-type="country-dropdown"
      {...inputProps}
    />
  );
}

CountryInputComponent.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  choices: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
};

export default function CountryInput({htmlId, htmlName, isRequired, choices, disabled}) {
  return (
    <FinalField
      id={htmlId}
      name={htmlName}
      component={CountryInputComponent}
      required={isRequired}
      choices={choices}
      clearable={!isRequired}
      parse={x => x}
      disabled={disabled}
    />
  );
}

CountryInput.propTypes = {
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  isRequired: PropTypes.bool,
  disabled: PropTypes.bool,
  choices: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
};

CountryInput.defaultProps = {
  isRequired: false,
  disabled: false,
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
