// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {Translate} from 'indico/react/i18n';

export default function InputCountry({htmlName, disabled, choices}) {
  return (
    <select name={htmlName} disabled={disabled}>
      <option key="" value="">
        {Translate.string('Select a country')}
      </option>
      {choices.map(country => (
        <option key={country.countryKey} value={country.countryKey}>
          {country.caption}
        </option>
      ))}
    </select>
  );
}

InputCountry.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  choices: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
};

InputCountry.defaultProps = {
  disabled: false,
};
