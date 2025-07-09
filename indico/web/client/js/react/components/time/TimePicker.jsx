// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useMemo, useState, useRef} from 'react';

import {useNativeEvent} from 'indico/react/hooks';
import {Translate, PluralTranslate} from 'indico/react/i18n';
import {Time, timeList} from 'indico/utils/time_value.js';

import {timeString} from './prop_types.js';

import 'indico/custom_elements/ind_time_picker.js';
import './TimePicker.module.scss';

const DEFAULT_STEP_SIZE = 15; // minutes
const TIME_FORMAT_PLACEHOLDER = {
  '12h': '--:-- AM/PM',
  '24h': '--:--',
};

function formatDuration(duration) {
  const durationInMins = duration.value;
  if (durationInMins < 60) {
    return PluralTranslate.string('{time} min', '{time} mins', durationInMins, {
      time: durationInMins,
    });
  }
  if (durationInMins % 30 === 0) {
    // 'Nice' hours like, either whole or half-hour
    const durationInHours = durationInMins / 60;
    return PluralTranslate.string('{time} hr', '{time} hrs', durationInHours, {
      time: durationInHours,
    });
  }
  // 'Ugly' hours, like 1:15, 1:05, won't display well as decimals
  return duration.toShortString();
}

function getOptions(currentValue, startTime, step, minTime, maxTime, timeFormat) {
  return timeList({
    markCurrent: currentValue,
    startTime,
    step,
    minTime,
    maxTime,
    timeFormat,
  }).map(option => {
    const {label, time, duration, disabled} = option;

    const itemProps = {};

    if (disabled) {
      itemProps['aria-disabled'] = true;
    }

    return (
      <li role="option" data-value={label} data-time={time} key={time} {...itemProps}>
        <time dateTime={time} styleName="option-label">
          <span>{label}</span>
          {duration ? (
            <>
              {' '}
              <span>({formatDuration(duration)})</span>
            </>
          ) : null}
        </time>
      </li>
    );
  });
}

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
  const [inputValue, setInputValue] = useState(
    value && Time.fromString(value, '24h').toFormattedString(timeFormat)
  );
  const [notice, setNotice] = useState('');
  const placeholder = TIME_FORMAT_PLACEHOLDER[timeFormat];

  const options = useMemo(() => getOptions(value, startTime, step, min, max, timeFormat), [
    value,
    startTime,
    step,
    min,
    max,
    timeFormat,
  ]);

  // Auto-clear notice
  useEffect(() => {
    if (!notice) {
      return;
    }

    const timer = setTimeout(() => {
      setNotice('');
    }, 10000);

    return () => clearTimeout(timer);
  }, [notice]);

  useEffect(
    () => {
      const propTime = Time.fromString(value, '24h');
      const internalTime = Time.fromString(inputValue, 'any');

      // Using Object.is() as value can also be NaN
      if (!Object.is(propTime.value, internalTime.value)) {
        setInputValue(propTime.toFormattedString(timeFormat));
      }
    },
    // The purpose of this hook is to sync the prop changes to the
    // input value *only* in cases where the prop was change without
    // first changing the input value. Therefore, the only valid
    // dependencies are the props. Adding anything from the local state
    // here would have undesired consequences.
    //
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [value, timeFormat]
  );

  const handleChange = ev => {
    setInputValue(ev.target.value);
    const newTime = Time.fromString(ev.target.value, 'any');
    onChange(newTime.isValid ? newTime.toString() : '');
  };

  const handleBlur = ev => {
    // Reformat the value when user leaves the field

    const maybeTime = Time.fromString(ev.target.value);
    const maybeFixedValue = Number.isNaN(maybeTime.value)
      ? ''
      : maybeTime.toFormattedString(timeFormat);

    // Value was already fixed?
    if (maybeFixedValue === ev.target.value) {
      return;
    }

    setInputValue(maybeFixedValue);

    // Announce any changes to screen readers

    if (!maybeFixedValue) {
      setNotice(
        Translate.string('The time value was invalid and was cleared', {
          time: maybeFixedValue,
        })
      );
    } else {
      setNotice(
        Translate.string('The time value was automatically formatted as {time}', {
          time: maybeFixedValue,
        })
      );
    }
  };

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
            <Translate as="span">Clear the time picker</Translate>
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
  onChange: PropTypes.func,
  value: PropTypes.string,
  startTime: timeString,
  step: PropTypes.number, // minutes
  min: timeString,
  max: timeString,
  timeFormat: PropTypes.oneOf(['24h', '12h']),
  required: PropTypes.bool,
};

TimePicker.defaultProps = {
  onChange: undefined,
  value: '',
  startTime: '',
  step: DEFAULT_STEP_SIZE,
  min: '0:00',
  max: '23:59',
  timeFormat: '24h',
  required: false,
};
