// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Dropdown, Form} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import '../../../styles/regform.module.scss';

const isoToFlag = country =>
  String.fromCodePoint(...country.split('').map(c => c.charCodeAt() + 0x1f1a5));

export default function CountryInput({htmlName, disabled, choices, title, isRequired}) {
  return (
    <Form.Field required={isRequired} disabled={disabled} styleName="field">
      <label>{title}</label>
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
