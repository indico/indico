// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Dropdown} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import '../../../styles/regform.module.scss';

const isoToFlag = country =>
  String.fromCodePoint(...country.split('').map(c => c.charCodeAt() + 0x1f1a5));

export default function CountryInput({htmlName, choices}) {
  return (
    <Dropdown
      styleName="country-dropdown"
      placeholder={Translate.string('Select a country')}
      name={htmlName}
      fluid
      search
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
  htmlName: PropTypes.string.isRequired,
  choices: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
};
