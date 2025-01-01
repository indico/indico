// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useCallback, useMemo, useState} from 'react';
import {Dropdown, Label} from 'semantic-ui-react';

import {SUIPalette} from 'indico/utils/palette';

const renderColorLabel = colorName => (
  <div style={{display: 'flex', alignItems: 'center'}}>
    <Label color={colorName} /> <span style={{marginLeft: 10}}>{SUIPalette[colorName]}</span>
  </div>
);

const availableColors = Object.keys(SUIPalette).map(colorName => ({
  text: renderColorLabel(colorName),
  value: colorName,
}));

export default function WTFSUIColorPicker({fieldId, required, disabled}) {
  const field = useMemo(() => document.getElementById(`${fieldId}-data`), [fieldId]);
  const [color, setColor] = useState(field.value);

  const updateColor = useCallback(
    (evt, {value}) => {
      field.value = value;
      setColor(value);
      field.dispatchEvent(new Event('change', {bubbles: true}));
    },
    [field]
  );

  return (
    <Dropdown
      value={color}
      options={availableColors}
      selection
      selectOnNavigation={false}
      selectOnBlur={false}
      clearable={!required}
      required={required}
      disabled={disabled}
      onChange={updateColor}
    />
  );
}

WTFSUIColorPicker.propTypes = {
  fieldId: PropTypes.string.isRequired,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
};

WTFSUIColorPicker.defaultProps = {
  required: false,
  disabled: false,
};
