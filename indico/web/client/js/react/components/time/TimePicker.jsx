// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useMemo, useState} from 'react';

import ComboBox from 'indico/react/components/ComboBox';
import {Translate} from 'indico/react/i18n';

import {timeString} from './prop_types.js';
import {Time, timeList} from './time_value.js';

import './TimePicker.module.scss';

const DEFAULT_STEP_SIZE = 15; // minutes
const TIME_FORMAT_PLACEHOLDER = {
  '12h': '--:-- AM/PM',
  '24h': '--:--',
};
const TIME_FORMAT_LOCALE = {
  '12h': 'en-US',
  '24h': 'de',
};

function TimeOptionLabel({value, label, duration}) {
  return (
    <time dateTime={value}>
      <span>{label}</span>
      {duration ? <span>{duration}</span> : null}
    </time>
  );
}

TimeOptionLabel.propTypes = {
  value: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  duration: PropTypes.string.isRequired,
};

function getOptions(currentValue, startTime, step, min, max, timeFormat) {
  return timeList({
    markCurrent: currentValue,
    startTime,
    step,
    min,
    max,
    locale: TIME_FORMAT_LOCALE[timeFormat],
    timeFormat,
  }).map(option => {
    const {label, time, duration, disabled} = option;

    return {
      value: label,
      disabled,
      label: <TimeOptionLabel value={time} label={label} duration={duration} />,
    };
  });
}

function formatTimeString(value, timeFormat) {
  if (!value) {
    return '';
  }

  const time = Time.fromString(value, timeFormat);
  if (isNaN(time.value)) {
    return '';
  }

  return time.toLocaleString(TIME_FORMAT_LOCALE[timeFormat]);
}

function rankTimeOption(timeFormat, _, keywordText, option) {
  const optionDisabled = option.hasAttribute('aria-disabled');
  const optionText = option.textContent.replace(/\s+/g, '').toLowerCase();
  const optionValue = option.firstElementChild.dateTime;
  const keywordValue = Time.fromString(keywordText, timeFormat).toString();

  keywordText = keywordText.toLowerCase().replace(/\s+/, '');

  let optionRank = 0;

  if (keywordText && !optionDisabled) {
    if (keywordText === optionText) {
      optionRank += 1000;
    } else if (optionValue === keywordValue) {
      optionRank += 100;
    } else if (optionText.startsWith(keywordText)) {
      optionRank += 10;
    }
  }

  return optionRank;
}

export default function TimePicker({value, startTime, step, min, max, timeFormat, onChange}) {
  const [inputValue, setInputValue] = useState(formatTimeString(value, '24h'));
  const [notice, setNotice] = useState('');
  const valueAsTime = Time.fromString(value, '24h');

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
      const inputTime = Time.fromString(inputValue, 'any');
      // Using Object.is() as value can also be NaN
      if (!Object.is(valueAsTime.value, inputTime.value)) {
        setInputValue(valueAsTime.toLocaleString(TIME_FORMAT_LOCALE[timeFormat]));
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
    const newValue = ev.target.value;
    const formattedNewValue = Time.fromString(newValue).toString();
    setInputValue('any');
    onChange(formattedNewValue === 'Invalid time' ? '' : formattedNewValue);
  };

  const handleBlur = ev => {
    // Reformat the value when user leaves the field

    const maybeFixedValue = formatTimeString(ev.target.value, 'any');

    // Value was already fixed
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

  return (
    <>
      <ComboBox
        styleName="time-picker"
        data-time-format={timeFormat}
        value={inputValue}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder={TIME_FORMAT_PLACEHOLDER[timeFormat]}
        options={options}
        rankOption={rankTimeOption.bind(null, timeFormat)}
      />
      <span styleName="notice" aria-live="polite">
        {notice}
      </span>
    </>
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
};

TimePicker.defaultProps = {
  onChange: undefined,
  value: '',
  startTime: '',
  step: DEFAULT_STEP_SIZE,
  min: '',
  max: '',
  timeFormat: '24h',
};
