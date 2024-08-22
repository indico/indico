// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useRef} from 'react';

import 'indico/custom_elements/ind_combobox';

export default function ComboBox({options, onChange, autocomplete, ...inputProps}) {
  const inputRef = useRef();

  const ariaAutocomplete = autocomplete ? 'both' : 'none';

  return (
    <ind-combo-box>
      <input
        {...inputProps}
        onChange={onChange}
        ref={inputRef}
        type="text"
        role="combobox"
        autoComplete="off"
        aria-autocomplete={ariaAutocomplete}
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
    </ind-combo-box>
  );
}

ComboBox.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.oneOfType([
      PropTypes.element,
      PropTypes.string,
      PropTypes.arrayOf(PropTypes.oneOfType([PropTypes.string, PropTypes.element])),
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
  autocomplete: PropTypes.bool,
};

ComboBox.defaultProps = {
  disabled: false,
  onFocus: undefined,
  onBlur: undefined,
  autocomplete: false,
};
