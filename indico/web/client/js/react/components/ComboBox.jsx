// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useRef} from 'react';

import {useNativeEvent} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {optionPropType} from 'indico/react/util/propTypes';

import 'indico/custom_elements/ind_combo_box';

function DefaultLabel({option}) {
  return option.label ?? option.value;
}

DefaultLabel.propTypes = {
  option: optionPropType,
};

export default function ComboBox({
  options,
  onChange,
  optionComponent: Option,
  rankOption,
  useAutocomplete,
  value,
  ...inputProps
}) {
  const comboBoxRef = useRef();
  const inputRef = useRef();

  useNativeEvent(comboBoxRef, 'change', onChange);
  useEffect(() => {
    if (rankOption) {
      comboBoxRef.current.rankOption = rankOption;
    } else {
      delete comboBoxRef.current.rankOption;
    }
  }, [rankOption]);

  if (useAutocomplete) {
    inputProps['aria-autocomplete'] = 'both';
  }

  return (
    <ind-combo-box ref={comboBoxRef} value={value}>
      <input ref={inputRef} type="text" role="combobox" autoComplete="off" {...inputProps} />
      <ul role="listbox">
        {options.map(option => {
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
              <Option option={option} />
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
  useAutocomplete: PropTypes.bool,
  optionComponent: PropTypes.oneOfType([PropTypes.string, PropTypes.elementType]),
  rankOption: PropTypes.func,
};

ComboBox.defaultProps = {
  disabled: false,
  onFocus: undefined,
  onBlur: undefined,
  useAutocomplete: false,
  optionComponent: DefaultLabel,
  rankOption: undefined,
};
