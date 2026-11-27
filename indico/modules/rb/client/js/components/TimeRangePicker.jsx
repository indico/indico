// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';

import TimePicker from 'indico/react/components/time/TimePicker';
import {FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {serializeTime, toMoment} from 'indico/utils/date';
import {Time} from 'indico/utils/time_value';

import './TimeRangePicker.module.scss';

const STEP = 30;
const FIRST_START_OPTION = 6 * 60;

function serializeMinutes(minutes) {
  return new Time(minutes).toString();
}

export function reportTimeRangeValidity(container) {
  const invalidInput = container?.querySelector('ind-time-picker input:invalid');
  if (!invalidInput) {
    return true;
  }
  invalidInput.focus();
  return invalidInput.reportValidity();
}

export default function TimeRangePicker({startTime, endTime, onChange, disabled, minTime}) {
  const startValue = serializeTime(startTime) ?? '';
  const endValue = serializeTime(endTime) ?? '';
  const start = Time.fromString(startValue, '24h');
  const end = Time.fromString(endValue, '24h');
  const minimum = Time.fromString(minTime ?? '00:00', '24h').value;
  const duration =
    start.isValid && end.isValid && end.value > start.value ? end.value - start.value : STEP;

  const firstStartOption = Math.max(FIRST_START_OPTION, Math.ceil(minimum / STEP) * STEP);
  const firstEndOption = Math.min(
    Time.MAX_TIME,
    Math.max(minimum + 1, start.isValid ? start.value + STEP : FIRST_START_OPTION)
  );

  function updateStart(value) {
    const nextStart = Time.fromString(value, '24h').value;
    const nextEnd =
      end.isValid && nextStart < end.value
        ? end.value
        : Math.min(Time.MAX_TIME, nextStart + duration);
    onChange(toMoment(value, 'HH:mm'), toMoment(serializeMinutes(nextEnd), 'HH:mm'));
  }

  function updateEnd(value) {
    const nextEnd = Time.fromString(value, '24h').value;
    const nextStart =
      start.isValid && start.value >= minimum && start.value < nextEnd
        ? start.value
        : Math.max(minimum, nextEnd - duration);
    onChange(toMoment(serializeMinutes(nextStart), 'HH:mm'), toMoment(value, 'HH:mm'));
  }

  return (
    <fieldset styleName="time-range-picker">
      <legend styleName="legend">
        <Translate>Time range</Translate>
      </legend>
      <TimePicker
        label={Translate.string('Start time')}
        value={startValue}
        timeFormat="24h"
        min={serializeMinutes(minimum)}
        max="23:58"
        firstOption={serializeMinutes(firstStartOption)}
        step={STEP}
        onChange={updateStart}
        disabled={disabled}
        labelErrors
        required
      />
      <TimePicker
        label={Translate.string('End time')}
        value={endValue}
        timeFormat="24h"
        min={serializeMinutes(Math.min(Time.MAX_TIME, minimum + 1))}
        firstOption={serializeMinutes(firstEndOption)}
        durationStart={start.isValid ? startValue : undefined}
        step={STEP}
        onChange={updateEnd}
        disabled={disabled}
        labelErrors
        required
      />
    </fieldset>
  );
}

TimeRangePicker.propTypes = {
  startTime: PropTypes.object.isRequired,
  endTime: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  minTime: PropTypes.string,
};

TimeRangePicker.defaultProps = {
  disabled: false,
  minTime: null,
};

function ValuedTimeRangePicker({value, onChange, ...rest}) {
  const startTime = toMoment(value.startTime, 'HH:mm');
  const endTime = toMoment(value.endTime, 'HH:mm');
  const handleChange = (start, end) => {
    onChange({
      startTime: serializeTime(start),
      endTime: serializeTime(end),
    });
  };
  return (
    <TimeRangePicker startTime={startTime} endTime={endTime} onChange={handleChange} {...rest} />
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
