// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';

import TimeRangePickerBase from 'indico/react/components/time/TimeRangePicker';
import {FinalField} from 'indico/react/forms';
import {momentObject} from 'indico/react/util/propTypes';

import css from './TimeRangePicker.module.scss';

export default function TimeRangePicker({startTime, endTime, onChange, minTime, ...rest}) {
  const handleChange = ([start, end]) => {
    onChange(moment(start, 'HH:mm'), moment(end, 'HH:mm'));
  };

  return (
    <TimeRangePickerBase
      start={startTime.format('HH:mm')}
      end={endTime.format('HH:mm')}
      onChange={handleChange}
      min={minTime?.format('HH:mm')}
      required
      extraStyle={css['time-range-picker']}
      {...rest}
    />
  );
}

TimeRangePicker.propTypes = {
  startTime: momentObject.isRequired,
  endTime: momentObject.isRequired,
  onChange: PropTypes.func.isRequired,
  minTime: momentObject,
};

function ValuedTimeRangePicker({value, onChange, minTime, ...rest}) {
  const handleChange = ([startTime, endTime]) => {
    onChange({startTime, endTime});
  };

  return (
    <TimeRangePickerBase
      start={value.startTime}
      end={value.endTime}
      onChange={handleChange}
      min={minTime}
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
  minTime: PropTypes.string,
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
