// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Dropdown} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

export default function ExtensionList({value, disabled, onChange, onFocus, onBlur}) {
  const handleChange = (e, {value: newValue}) => {
    onChange(_.uniq(newValue.map(x => x.trim().replace(/^[*.]+/, ''))));
    onFocus();
    onBlur();
  };

  return (
    <Dropdown
      options={value.map(x => ({text: x, value: x}))}
      value={value}
      disabled={disabled}
      search
      selection
      multiple
      allowAdditions
      fluid
      icon={null}
      closeOnChange
      noResultsMessage={Translate.string('Enter an extension')}
      additionLabel={Translate.string('Add extension') + ' '} // eslint-disable-line prefer-template
      onChange={handleChange}
    />
  );
}

ExtensionList.propTypes = {
  value: PropTypes.arrayOf(PropTypes.string).isRequired,
  disabled: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
};
