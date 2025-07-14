// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useRef} from 'react';

import {useNativeEvent} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

export default function ComboBox({options, value, onChange, ...inputProps}) {
  const uncontrolledInputProps = {...inputProps, defaultValue: value};
  const inputRef = useRef();

  useNativeEvent(inputRef, 'input', onChange);
  useNativeEvent(inputRef, 'change', onChange);

  return (
    <ind-combo-box>
      <input
        ref={inputRef}
        {...uncontrolledInputProps}
        type="text"
        role="combobox"
        autoComplete="off"
      />
      <ul role="listbox">
        {options.map(function(option) {
          if (typeof option === 'string') {
            option = {
              value: option,
            };
          } else if (Array.isArray(option)) {
            option = {
              value: option[0],
              label: option[1],
            };
          }

          const optionProps = {};

          if (option.disabled) {
            optionProps['aria-disabled'] = true;
          }

          return (
            <li role="option" data-value={option.value} key={option.value} {...optionProps}>
              {option.label ?? option.value}
            </li>
          );
        })}
      </ul>
      {inputProps.required ? null : (
        <button type="button" value="clear" disabled={inputProps.disabled}>
          <Translate as="span">Clear the combobox</Translate>
        </button>
      )}
    </ind-combo-box>
  );
}

ComboBox.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.oneOfType([
      PropTypes.any,
      PropTypes.arrayOf(PropTypes.any),
      PropTypes.shape({
        value: PropTypes.any,
        label: PropTypes.oneOfType([PropTypes.string, PropTypes.element]),
        disabled: PropTypes.bool,
      }),
    ])
  ).isRequired,
  value: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func,
  onBlur: PropTypes.func,
};

ComboBox.defaultProps = {
  disabled: false,
  onFocus: undefined,
  onBlur: undefined,
};
