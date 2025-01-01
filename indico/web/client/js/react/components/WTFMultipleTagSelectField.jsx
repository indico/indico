// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useMemo, useState, useEffect} from 'react';
import {Dropdown, Label} from 'semantic-ui-react';

import {Translate} from '../i18n';

export default function WTFMultipleTagSelectField({fieldId, wrapperId, choices}) {
  const parentElement = useMemo(() => document.getElementById(wrapperId), [wrapperId]);
  const [selectedOptions, setSelectedOptions] = useState([]);

  // Trigger change only after the DOM has changed
  useEffect(() => {
    parentElement.dispatchEvent(new Event('change', {bubbles: true}));
  }, [selectedOptions, parentElement]);

  const handleChange = (e, {value}) => {
    setSelectedOptions(value);
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
    <div>
      <Dropdown
        fluid
        multiple
        onChange={handleChange}
        options={options}
        placeholder={Translate.string('Choose an option')}
        selection
        value={selectedOptions}
        renderLabel={renderLabel}
      />
      {/* Since Dropdown does not render as a <select> element, we use a dummy <select>
       * with the correct name attribute and options selected which are used when the form is submitted.
       */}
      <select
        id={fieldId}
        name={fieldId}
        multiple
        readOnly
        value={selectedOptions}
        style={{display: 'none'}}
      >
        {options.map(({key, text, value}) => (
          <option key={key} value={value}>
            {text}
          </option>
        ))}
      </select>
    </div>
  );
}

WTFMultipleTagSelectField.propTypes = {
  fieldId: PropTypes.string.isRequired,
  wrapperId: PropTypes.string.isRequired,
  choices: PropTypes.array.isRequired,
};
