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

import 'indico/custom_elements/ind_select';

export default function Select({
  options,
  value,
  onChange,
  disabled,
  required,
  className,
  ...inputProps
}) {
  const indSelectRef = useRef();

  // Boolean attributes need special treatment because React
  // sets attributes rather than properties on custom elements.
  if (disabled) {
    inputProps.disabled = disabled;
  }
  if (required) {
    inputProps.required = required;
  }
  if (className) {
    inputProps.class = className;
  }

  useNativeEvent(indSelectRef, 'change', onChange);

  return (
    <ind-select ref={indSelectRef} value={value} {...inputProps} data-clearable={!required}>
      <div className="caption" data-caption>
        <Translate>Select a choice</Translate>
      </div>
      {required ? null : (
        <button type="button" className="clear" value="clear" hidden>
          <span>Clear</span>
        </button>
      )}

      <dialog aria-label={Translate.string('Options')}>
        <label className="option-filter">
          <span>
            <Translate>Filter the options</Translate>
          </span>
          <input className="filter" type="text" autoComplete="off" aria-expanded="false" />
        </label>

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
                {option.label ?? option.value}
              </li>
            );
          })}
          <li className="no-option" hidden>
            <Translate>No option matches your keyword</Translate>
          </li>
        </ul>
      </dialog>
    </ind-select>
  );
}

Select.propTypes = {
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
  disabled: PropTypes.bool,
  required: PropTypes.bool,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  className: PropTypes.string,
};

Select.defaultProps = {
  disabled: false,
  required: false,
};
