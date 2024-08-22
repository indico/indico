// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useState, useMemo} from 'react';

import {ComboBox} from 'indico/react/components';
import {FinalField} from 'indico/react/forms';
import {PluralTranslate, Translate} from 'indico/react/i18n';
import * as time from 'indico/utils/time';

import './TimeRangePicker.module.scss';

// All times in this module are expressed in integer minutes since midnight.
// This allows us to perform simple arithmetic operations on time values without
// needing any specialized libraries. The conversion between the integer values
// and string values are done using the `utils/time.js` module.

const TIME_OPTIONS_STEP_SIZE = 30; // minutes
const DEFAULT_MIN_TIME = 360; // 6:00
const START_OF_DAY = 0; // 0:00
const END_OF_DAY = 1439; // 23:59

function humanizeDuration(duration) {
  const minutes = duration % 60;
  const hours = Math.floor((duration / 60) * 10) / 10;
  if (hours < 1) {
    return PluralTranslate.string('{time} min', '{time} min', minutes, {time: minutes});
  }
  return PluralTranslate.string('{time} hour', '{time} hours', hours, {time: hours});
}

function getStartTimeOptions(minTime) {
  const options = [];

  for (
    let value = minTime ?? DEFAULT_MIN_TIME;
    value < END_OF_DAY;
    value += TIME_OPTIONS_STEP_SIZE
  ) {
    options.push(time.toString(value));
  }

  return options;
}

function getEndTimeOptions(startTime) {
  const options = [];

  for (
    let value = startTime + TIME_OPTIONS_STEP_SIZE;
    value < END_OF_DAY;
    value += TIME_OPTIONS_STEP_SIZE
  ) {
    const duration = value - startTime;
    const timeStr = time.toString(value);
    options.push({
      value: timeStr,
      label: (
        <div styleName="time-with-duration">
          {timeStr} <span styleName="duration">({humanizeDuration(duration)})</span>
        </div>
      ),
    });
  }

  return options;
}

export default function TimeRangePickerMomentAdapter({
  startTime,
  endTime,
  minTime,
  onChange,
  ...props
}) {
  const startTimeStr = startTime?.format('HH:mm');
  const endTimeStr = endTime?.format('HH:mm');
  const minTimeStr = minTime?.format('HH:mm') ?? '';

  const handleChange = (start, end) => onChange(moment(start, 'HH:mm'), moment(end, 'HH:mm'));

  return (
    <TimeRangePicker
      startTime={startTimeStr}
      endTime={endTimeStr}
      minTime={minTimeStr}
      onChange={handleChange}
      {...props}
    />
  );
}

TimeRangePickerMomentAdapter.propTypes = {
  startTime: PropTypes.object.isRequired,
  endTime: PropTypes.object.isRequired,
  minTime: PropTypes.object,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
};

TimeRangePicker.defaultProps = {
  disabled: false,
  minTime: moment(time.toString(DEFAULT_MIN_TIME), 'HH:mm'),
};

function TimeRangePicker({startTime, endTime, onChange, disabled, minTime}) {
  const [startInputValue, setStartInputValue] = useState(time.normalize(startTime));
  const [endInputValue, setEndInputValue] = useState(time.normalize(endTime));
  const [promptText, setPromptText] = useState('');
  const startT = time.timeStrToInt(startTime);
  const endT = time.timeStrToInt(endTime);
  const minT = time.timeStrToInt(minTime);
  const duration = endT - startT;

  const startTimeOptions = useMemo(() => {
    return getStartTimeOptions(minT);
  }, [minT]);

  const endTimeOptions = useMemo(() => {
    return getEndTimeOptions(startT);
  }, [startT]);

  const emitChange = (start, end) => onChange(time.toString(start), time.toString(end));

  const updateStartTime = evt => {
    setStartInputValue(evt.target.value);

    const t = time.timeStrToInt(evt.target.value);

    console.log(evt.target.value, t);

    // Ignore invalid inputs
    if (!t || t < minT) {
      return;
    }

    // When start time is >= end time, move the end time to keep duration
    if (t >= endT) {
      const adjustedEndT = Math.min(t + duration, END_OF_DAY);
      if (adjustedEndT === t) {
        emitChange(adjustedEndT - duration, adjustedEndT);
      } else {
        emitChange(t, adjustedEndT);
      }
      return;
    }

    // Happy path
    emitChange(t, endT);
  };

  const updateEndTime = evt => {
    setEndInputValue(evt.target.value);

    const t = time.timeStrToInt(evt.target.value);

    // Ignore invalid inputs
    if (!t || t < minTime) {
      return;
    }

    // When end time is <= start time, move the start time to maintain the duration
    if (t <= startT) {
      const adjustedStartT = Math.max(t - duration, START_OF_DAY);
      if (adjustedStartT === t) {
        emitChange(adjustedStartT, adjustedStartT + duration);
      } else {
        emitChange(adjustedStartT, t);
      }
      return;
    }

    // Happy path
    emitChange(startT, t);
  };

  const fixInputValues = () => {
    const startTimeStr = time.toString(startT);
    const endTimeStr = time.toString(endT);
    let fixedStart = false;
    let fixedEnd = false;

    if (startInputValue !== startTimeStr) {
      setStartInputValue(startTimeStr);
      fixedStart = true;
    }

    if (endInputValue !== endTimeStr) {
      setEndInputValue(endTimeStr);
      fixedEnd = true;
    }

    switch (true) {
      case fixedStart && fixedEnd:
        setPromptText(
          Translate.string('The times have been adjusted to {start} and {end}.', {
            start: startTimeStr,
            end: endTimeStr,
          })
        );
        break;
      case fixedStart:
        setPromptText(
          Translate.string('The start time has been adjusted to {start}.', {start: startTimeStr})
        );
        break;
      case fixedEnd:
        setPromptText(
          Translate.string('The end time has been adjusted to {end}.', {end: endTimeStr})
        );
        break;
    }
  };

  return (
    <div styleName="time-range-picker">
      <ComboBox
        onChange={updateStartTime}
        onBlur={fixInputValues}
        options={startTimeOptions}
        value={startInputValue}
        disabled={disabled}
      />
      <ComboBox
        onChange={updateEndTime}
        onBlur={fixInputValues}
        options={endTimeOptions}
        value={endInputValue}
        disabled={disabled}
      />

      <div styleName="prompt" aria-live="polite">
        {/* Prompt text is used to provide cues to the screen readers
              about how the entered input is going to be interpreted
              by the application. */}
        {promptText}
      </div>
    </div>
  );
}

TimeRangePicker.propTypes = {
  startTime: PropTypes.string.isRequired,
  endTime: PropTypes.string.isRequired,
  minTime: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
};

TimeRangePicker.defaultProps = {
  disabled: false,
  minTime: DEFAULT_MIN_TIME,
};

function ValuedTimeRangePicker({value, onChange, ...rest}) {
  const handleChange = (startTime, endTime) => onChange({startTime, endTime});
  return (
    <TimeRangePicker
      startTime={value.startTime}
      endTime={value.endTime}
      onChange={handleChange}
      {...rest}
    />
  );
}

ValuedTimeRangePicker.propTypes = {
  value: PropTypes.exact({
    startTime: PropTypes.string.isRequired,
    endTime: PropTypes.string.isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};

/**
 * Like `FinalField` but for a `TimeRangePicker`.
 */
export function FinalTimeRangePicker({name, ...rest}) {
  return <FinalField name={name} component={ValuedTimeRangePicker} isEqual={_.isEqual} {...rest} />;
}

FinalTimeRangePicker.propTypes = {
  name: PropTypes.string.isRequired,
};
