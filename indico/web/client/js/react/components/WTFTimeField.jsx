// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import TimePicker from 'rc-time-picker';
import React, {useEffect, useMemo, useRef, useState, useCallback} from 'react';

import {toMoment} from 'indico/utils/date';

export default function WTFTimeField({timeId, uses24HourFormat, required, disabled}) {
  const timeField = useMemo(() => document.getElementById(timeId), [timeId]);
  const [time, setTime] = useState(toMoment(timeField.value, 'HH:mm', true));
  const format = uses24HourFormat ? 'H:mm' : 'h:mm a';
  const timePickerRef = useRef(null);

  const updateTime = useCallback(
    value => {
      timeField.value = value ? value.format('HH:mm') : '';
      setTime(value);
      timeField.dispatchEvent(new Event('change', {bubbles: true}));
    },
    [timeField]
  );

  useEffect(() => {
    timePickerRef.current.picker.required = required;
  }, [required]);

  return (
    <TimePicker
      showSecond={false}
      value={time}
      focusOnOpen
      format={format}
      onChange={updateTime}
      use12Hours={!uses24HourFormat}
      allowEmpty={false}
      placeholder="--:--"
      disabled={disabled}
      ref={timePickerRef}
      // keep the picker in the DOM tree of the surrounding element to avoid
      // e.g. qbubbles from closing when a picker is used inside one and the
      // user clicks something in the picker
      getPopupContainer={node => node}
    />
  );
}

WTFTimeField.propTypes = {
  timeId: PropTypes.string.isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
};

WTFTimeField.defaultProps = {
  required: false,
  disabled: false,
};
