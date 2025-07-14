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

import {commonDefaults, commonProps, timeString} from './prop_types.js';
import {
  TIME_FORMAT_PLACEHOLDER,
  useHandleBlur,
  useInputValue,
  useNotice,
  useOptions,
} from './shared.js';

import 'indico/custom_elements/ind_time_picker.js';
import './time.module.scss';

export default function TimePicker({
  value,
  startTime,
  step,
  min,
  max,
  timeFormat,
  onChange,
  ...inputProps
}) {
  const pickerRef = useRef();
  const placeholder = TIME_FORMAT_PLACEHOLDER[timeFormat];

  const [inputValue, setInputValue, handleChange] = useInputValue(value, timeFormat, onChange);
  const [notice, setNotice] = useNotice();
  const options = useOptions(value, startTime, step, min, max, timeFormat);
  const handleBlur = useHandleBlur(
    timeFormat,
    setInputValue,
    () => setNotice(Translate.string('The time value was invalid and was cleared')),
    time =>
      setNotice(Translate.string('The time value was automatically formatted as {time}', {time}))
  );

  useNativeEvent(pickerRef, 'change', handleChange);

  return (
    <div styleName="time-picker">
      <ind-time-picker ref={pickerRef} value={inputValue}>
        <input
          type="text"
          role="combobox"
          autoComplete="off"
          placeholder={placeholder}
          onBlur={handleBlur}
          data-time-format={timeFormat}
          {...inputProps}
        />
        <ul role="listbox">{options}</ul>
        {inputProps.required ? null : (
          <button type="button" value="clear" disabled={inputProps.disabled}>
            <Translate as="span">Clear the time</Translate>
          </button>
        )}
      </ind-time-picker>
      <span styleName="notice" aria-live="polite">
        {notice}
      </span>
    </div>
  );
}

TimePicker.propTypes = {
  value: PropTypes.string,
  startTime: timeString,
  ...commonProps,
};

TimePicker.defaultProps = {
  value: '',
  startTime: '',
  ...commonDefaults,
};
