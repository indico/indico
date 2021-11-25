// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import '../../../styles/regform.module.scss';

export default function CountryInput({htmlName, disabled, choices, title, isRequired}) {
  return (
    <Form.Field required={isRequired} disabled={disabled} styleName="field">
      <label>{title}</label>
      <select name={htmlName}>
        <option key="" value="">
          {Translate.string('Select a country')}
        </option>
        {choices.map(country => (
          <option key={country.countryKey} value={country.countryKey}>
            {country.caption}
          </option>
        ))}
      </select>
    </Form.Field>
  );
}

CountryInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  choices: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
  title: PropTypes.string.isRequired,
  isRequired: PropTypes.bool.isRequired,
};

CountryInput.defaultProps = {
  disabled: false,
};
