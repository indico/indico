// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useRef} from 'react';

import 'indico/custom_elements/ind_combobox';
import {useNativeEvent} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

export default function Combobox({options, value, onChange, ...inputProps}) {
  const uncontrolledInputProps = {...inputProps, defaultValue: value};
  const inputRef = useRef();

  useNativeEvent(inputRef, 'input', onChange);
  useNativeEvent(inputRef, 'change', onChange);

  return (
    <ind-combobox>
      <input ref={inputRef} {...uncontrolledInputProps} type="text" role="combobox" />
      <ul role="listbox">
        {options.map(function(valueLabel) {
          let optionLabel, optionValue;
          if (typeof valueLabel === 'string') {
            optionLabel = valueLabel;
            optionValue = valueLabel;
          } else {
            [optionValue, optionLabel] = valueLabel;
          }

          return (
            <li role="option" data-value={optionValue} key={optionValue}>
              {optionLabel}
            </li>
          );
        })}
      </ul>
      <button type="button" value="clear">
        <Translate as="span">Clear the combobox</Translate>
      </button>
    </ind-combobox>
  );
}

Combobox.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.arrayOf(PropTypes.oneOfType([PropTypes.string, PropTypes.element])),
    ])
  ).isRequired,
  value: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func,
  onBlur: PropTypes.func,
};

Combobox.defaultProps = {
  disabled: false,
  onFocus: undefined,
  onBlur: undefined,
};
