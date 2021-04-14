// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import TimePicker from 'rc-time-picker';
import React, {useEffect, useMemo, useRef, useState, useCallback} from 'react';

const timeToSeconds = time => (time ? time.diff(moment().startOf('day'), 'seconds') : null);
const secondsToTime = seconds =>
  moment()
    .startOf('day')
    .seconds(seconds);

export default function WTFDurationField({timeId, required, disabled}) {
  const timeField = useMemo(() => document.getElementById(timeId), [timeId]);
  const [time, setTime] = useState(secondsToTime(timeField.value));
  const timePickerRef = useRef(null);

  const handleTimePickerChange = useCallback(
    value => {
      setTime(value || null);
      timeField.value = timeToSeconds(value);
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
      format="H:mm"
      onChange={handleTimePickerChange}
      allowEmpty={false}
      placeholder="h:mm"
      disabled={disabled}
      ref={timePickerRef}
      // keep the picker in the DOM tree of the surrounding element to avoid
      // e.g. qbubbles from closing when a picker is used inside one and the
      // user clicks something in the picker
      getPopupContainer={node => node}
    />
  );
}

WTFDurationField.propTypes = {
  timeId: PropTypes.string.isRequired,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
};

WTFDurationField.defaultProps = {
  required: false,
  disabled: false,
};
