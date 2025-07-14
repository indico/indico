// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useMemo, useState} from 'react';
import {Dropdown, Label} from 'semantic-ui-react';

import {Translate} from '../i18n';

export default function WTFMultipleTagSelectField({fieldId, choices, inputArgs, initialSelection}) {
  const selectField = useMemo(() => document.getElementById(fieldId), [fieldId]);
  const [selectedOptions, setSelectedOptions] = useState(initialSelection);

  const handleChange = (e, {value}) => {
    setSelectedOptions(value);
    [...selectField.querySelectorAll('option')].forEach(opt => {
      opt.selected = value.includes(opt.value);
    });
    selectField.dispatchEvent(new Event('change', {bubbles: true}));
  };

  const renderLabel = label => ({
    content: label.text,
    color: label.color,
    style: {
      boxShadow: 'none',
      padding: '6px 10px',
    },
  });

  const options = choices.map(([id, [title, color]]) => ({
    key: id,
    text: title,
    value: id,
    color,
    content: <Label color={color}>{title}</Label>,
  }));

  return (
    <Dropdown
      fluid
      multiple
      onChange={handleChange}
      options={options}
      placeholder={Translate.string('Choose an option')}
      selection
      value={selectedOptions}
      renderLabel={renderLabel}
      disabled={inputArgs.disabled ?? false}
    />
  );
}

WTFMultipleTagSelectField.propTypes = {
  fieldId: PropTypes.string.isRequired,
  choices: PropTypes.array.isRequired,
  inputArgs: PropTypes.object.isRequired,
  initialSelection: PropTypes.array.isRequired,
};
