// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useRef} from 'react';

import './Checkbox.module.scss';

export default function Checkbox({
  label,
  onChange,
  indeterminate,
  showAsToggle,
  className,
  style,
  ...inputProps
}) {
  const checkbox = useRef();

  useEffect(() => {
    checkbox.current.indeterminate = indeterminate;
  }, [indeterminate]);

  // Props fixup
  inputProps.type = 'checkbox';
  if (showAsToggle) {
    inputProps['data-as-toggle'] = true;
  }

  const handleChange = evt => {
    if (onChange) {
      onChange(evt, {checked: evt.target.checked});
    }
  };

  return (
    <label className={className} style={style} styleName="checkbox-field">
      <span styleName="checkbox-label">
        <input ref={checkbox} styleName="checkbox" onChange={handleChange} {...inputProps} />
        <span>
          {label}
          {inputProps.required && (
            <span styleName="required-checkbox-asterisk" aria-hidden="true">
              *
            </span>
          )}
        </span>
      </span>
    </label>
  );
}

Checkbox.propTypes = {
  label: PropTypes.oneOfType([PropTypes.string, PropTypes.element]).isRequired,
  onChange: PropTypes.func,
  indeterminate: PropTypes.bool,
  showAsToggle: PropTypes.bool,
  className: PropTypes.string,
  style: PropTypes.object,
};

Checkbox.defaultProps = {
  indeterminate: false,
  showAsToggle: false,
  className: '',
  style: {},
};
