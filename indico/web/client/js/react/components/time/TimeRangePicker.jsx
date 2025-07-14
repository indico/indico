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

import {timeString, commonDefaults, commonProps} from './prop_types.js';
import {
  TIME_FORMAT_PLACEHOLDER,
  useHandleBlur,
  useInputValue,
  useNotice,
  useOptions,
} from './shared.js';

import 'indico/custom_elements/ind_time_picker.js';
import './time.module.scss';

function TimePicker({pickerRef, value, timeFormat, options, ...inputProps}) {
  return (
    <ind-time-picker ref={pickerRef} value={value}>
      <input
        type="text"
        role="combobox"
        autoComplete="off"
        data-time-format={timeFormat}
        {...inputProps}
      />
      <ul role="listbox">{options}</ul>
      {inputProps.required ? null : (
        <button type="button" value="clear" disabled={inputProps.disabled}>
          <Translate as="span">Clear the time picker</Translate>
        </button>
      )}
    </ind-time-picker>
  );
}

TimePicker.propTypes = {
  pickerRef: PropTypes.oneOfType([PropTypes.func, PropTypes.object]).isRequired,
  value: PropTypes.string.isRequired,
  placeholder: PropTypes.string.isRequired,
  timeFormat: PropTypes.string.isRequired,
  options: PropTypes.arrayOf(PropTypes.element).isRequired,
};

export default function TimeRangePicker({
  start,
  end,
  step,
  min,
  max,
  timeFormat,
  onChange,
  extraStyle,
  ...inputProps
}) {
  const startPickerRef = useRef();
  const endPickerRef = useRef();

  const placeholder = TIME_FORMAT_PLACEHOLDER[timeFormat];

  const onStartChange = newStart => onChange([newStart, end]);
  const onEndChange = newEnd => onChange([start, newEnd]);

  const [startValue, setStartValue, handleStartChange] = useInputValue(
    start,
    timeFormat,
    onStartChange
  );
  const [endValue, setEndValue, handleEndChange] = useInputValue(end, timeFormat, onEndChange);

  const [notice, setNotice] = useNotice();

  const startOptions = useOptions(start, '', step, min, max, timeFormat);
  const endOptions = useOptions(end, start, step, min, max, timeFormat);

  const handleStartBlur = useHandleBlur(
    timeFormat,
    setStartValue,
    () => setNotice(Translate.string('The start time was invalid and was cleared')),
    time =>
      setNotice(Translate.string('The start time was automatically formatted as {time}', {time}))
  );
  const handleEndBlur = useHandleBlur(
    timeFormat,
    setEndValue,
    () => setNotice(Translate.string('The end time was invalid and was cleared')),
    time =>
      setNotice(Translate.string('The end time was automatically formatted as {time}', {time}))
  );

  useNativeEvent(startPickerRef, 'change', handleStartChange);
  useNativeEvent(endPickerRef, 'change', handleEndChange);

  return (
    <fieldset styleName="time-range-picker" className={extraStyle}>
      <legend>
        <Translate>Select a time range</Translate>
      </legend>

      <TimePicker
        pickerRef={startPickerRef}
        value={startValue}
        timeFormat={timeFormat}
        options={startOptions}
        placeholder={placeholder}
        onBlur={handleStartBlur}
        {...inputProps}
      />

      <TimePicker
        pickerRef={endPickerRef}
        value={endValue}
        timeFormat={timeFormat}
        options={endOptions}
        placeholder={placeholder}
        onBlur={handleEndBlur}
        {...inputProps}
      />

      <span styleName="notice" aria-live="polite">
        {notice}
      </span>
    </fieldset>
  );
}

TimeRangePicker.propTypes = {
  start: timeString,
  end: timeString,
  step: PropTypes.number,
  min: timeString,
  max: timeString,
  timeFormat: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  extraStyle: PropTypes.string,
  ...commonProps,
};

TimeRangePicker.defaultProps = {
  start: '',
  end: '',
  step: 15,
  min: '00:00',
  max: '23:59',
  extraStyle: '',
  ...commonDefaults,
};
