// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import TimePicker from 'rc-time-picker';
import React, {useState} from 'react';

import {SingleDatePicker} from 'indico/react/components';
import {FinalDropdown} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

export default function DateInput({htmlName, id, disabled, dateFormat, hasTime}) {
  const [date, setDate] = useState(null);
  const [time, setTime] = useState(null);
  const uses24HourFormat = true; // TODO: depend on the selected format string
  const timeDateFormat = dateFormat
    .replace(/%([HMdmY])/g, (match, c) => ({H: 'HH', M: 'mm', d: 'DD', m: 'MM', Y: 'YYYY'}[c]))
    .split(' ');

  if (dateFormat.includes('%d')) {
    return (
      <>
        <SingleDatePicker
          id={`regform-datepicker-${id}`}
          date={date}
          onDateChange={setDate}
          placeholder={timeDateFormat[0]}
          displayFormat={timeDateFormat[0]}
          disabled={disabled}
          isOutsideRange={() => false}
          enableOutsideDays
          noBorder
          small
        />
        {hasTime && (
          <TimePicker
            id={`regform-timepicker-${id}`}
            showSecond={false}
            value={time}
            focusOnOpen
            format={timeDateFormat[1]}
            onChange={setTime}
            use12Hours={!uses24HourFormat}
            allowEmpty={false}
            placeholder="--:--"
            disabled={disabled}
            getPopupContainer={node => node}
          />
        )}
      </>
    );
  } else {
    return (
      <input type="text" name={htmlName} placeholder={timeDateFormat[0]} disabled={disabled} />
    );
  }
}

DateInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  id: PropTypes.number.isRequired,
  disabled: PropTypes.bool,
  dateFormat: PropTypes.oneOf([
    '%d/%m/%Y %H:%M',
    '%d.%m.%Y %H:%M',
    '%m/%d/%Y %H:%M',
    '%m.%d.%Y %H:%M',
    '%Y/%m/%d %H:%M',
    '%Y.%m.%d %H:%M',
    '%d/%m/%Y',
    '%d.%m.%Y',
    '%m/%d/%Y',
    '%m.%d.%Y',
    '%Y/%m/%d',
    '%Y.%m.%d',
    '%m/%Y',
    '%m.%Y',
    '%Y',
  ]).isRequired,
  hasTime: PropTypes.bool,
};

DateInput.defaultProps = {
  disabled: false,
  hasTime: false,
};

export const dateSettingsInitialData = {
  dateFormat: '%d/%m/%Y',
};

export function DateSettings() {
  const options = [
    '%d/%m/%Y %H:%M',
    '%d.%m.%Y %H:%M',
    '%m/%d/%Y %H:%M',
    '%m.%d.%Y %H:%M',
    '%Y/%m/%d %H:%M',
    '%Y.%m.%d %H:%M',
    '%d/%m/%Y',
    '%d.%m.%Y',
    '%m/%d/%Y',
    '%m.%d.%Y',
    '%Y/%m/%d',
    '%Y.%m.%d',
    '%m/%Y',
    '%m.%Y',
    '%Y',
  ].map(opt => ({
    key: opt,
    value: opt,
    text: opt.replace(
      /%([HMdmY])/g,
      (match, c) => ({H: 'hh', M: 'mm', d: 'DD', m: 'MM', Y: 'YYYY'}[c])
    ),
  }));
  return (
    <FinalDropdown
      name="dateFormat"
      label={Translate.string('Date format')}
      options={options}
      required
      selection
    />
  );
}
