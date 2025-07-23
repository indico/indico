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
import {Time} from 'indico/utils/time_value.js';

import {timeString, commonDefaults, commonProps} from './prop_types.js';
import {
  TIME_FORMAT_PLACEHOLDER,
  createBlurHandler,
  useInputValue,
  useNotice,
  useOptions,
  useSyncInputWithProp,
} from './shared.js';

import 'indico/custom_elements/ind_time_picker.js';
import './time.module.scss';

const getStartTimeClearedMessage = () =>
  Translate.string('The start time was invalid and was cleared');
const getStartTimeFormattedMessage = time =>
  Translate.string('The start time was automatically formatted as {time}', {time});
const getEndTimeClearedMessage = () => Translate.string('The end time was invalid and was cleared');
const getEndTimeFormattedMessage = time =>
  Translate.string('The end time was automatically formatted as {time}', {time});

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

  const [notice, setNotice] = useNotice();
  const [startValue, setStartValue] = useInputValue(start, timeFormat);
  const [endValue, setEndValue] = useInputValue(end, timeFormat);
  // Calculate duration from the prop values, not the input field values
  const duration = Time.fromString(start, '24h').duration(Time.fromString(end, '24h'));

  useSyncInputWithProp(start, startValue, setStartValue, timeFormat);
  useSyncInputWithProp(end, endValue, setEndValue, timeFormat);

  const startOptions = useOptions(start, '', step, min, max, timeFormat);
  const endOptions = useOptions(end, start, step, min, max, timeFormat);

  const sendChangeUpstream = (startTimeString, endTimeString) => {
    onChange([startTimeString, endTimeString]);
  };

  const handleStartTimeChange = newStartTimeString => {
    const newStartTime = Time.fromString(newStartTimeString, '24h');
    let newEndTime = new Time(newStartTime.value).addDuration(duration);

    if (newEndTime.isValid) {
      const newEndTimeString = newEndTime.toFormattedString(timeFormat);
      setEndValue(newEndTimeString);
    } else {
      newEndTime = Time.fromString(endValue, timeFormat);
    }

    sendChangeUpstream(newStartTime.toSafeString(), newEndTime.toSafeString());
  };

  const handleEndTimeChange = newEndTimeString => {
    const newEndTime = Time.fromString(newEndTimeString, '24h');
    const startTime = Time.fromString(startValue, timeFormat);
    let newStartTime = startTime;

    if (startTime.value > newEndTime.value) {
      newStartTime = new Time(Math.max(0, newEndTime.value - step));
    }

    sendChangeUpstream(newStartTime.toSafeString(), newEndTime.toSafeString());
  };

  const handleStartBlur = createBlurHandler(
    timeFormat,
    setStartValue,
    handleStartTimeChange,
    setNotice,
    getStartTimeClearedMessage,
    getStartTimeFormattedMessage
  );

  const handleEndBlur = createBlurHandler(
    timeFormat,
    setEndValue,
    handleEndTimeChange,
    setNotice,
    getEndTimeClearedMessage,
    getEndTimeFormattedMessage
  );

  const handleStartChange = evt => {
    setStartValue(evt.target.value);
  };

  const handleEndChange = evt => {
    setEndValue(evt.target.value);
  };

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
