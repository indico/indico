// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {Button} from 'semantic-ui-react';

import {FinalField, unsortedArraysEqual} from 'indico/react/forms';

export function WeekdayRecurrencePicker({onChange, value, disabled, requireOneSelected}) {
  const WEEKDAYS = moment.weekdays(true).map(wd => ({
    value: moment()
      .day(wd)
      .locale('en')
      .format('ddd')
      .toLowerCase(),
    text: moment()
      .isoWeekday(wd)
      .format('ddd'),
  }));

  const handleDayClick = day => {
    const selected = value.includes(day);
    if (disabled || (requireOneSelected && selected && value.length === 1)) {
      return;
    }
    let newValue;
    if (selected) {
      newValue = value.filter(v => v !== day);
    } else {
      newValue = [...value, day];
    }
    newValue.sort();
    onChange(newValue);
  };

  return (
    <div>
      <Button.Group>
        {WEEKDAYS.map(weekday => (
          <Button
            type="button"
            key={weekday.value}
            value={weekday.value}
            compact
            disabled={disabled}
            primary={value.includes(weekday.value)}
            onClick={() => handleDayClick(weekday.value)}
          >
            {weekday.text}
          </Button>
        ))}
      </Button.Group>
    </div>
  );
}

WeekdayRecurrencePicker.propTypes = {
  onChange: PropTypes.func.isRequired,
  value: PropTypes.arrayOf(PropTypes.string),
  disabled: PropTypes.bool,
  requireOneSelected: PropTypes.bool,
};

WeekdayRecurrencePicker.defaultProps = {
  value: [],
  disabled: false,
  requireOneSelected: false,
};

export default WeekdayRecurrencePicker;

export function FinalWeekdayRecurrencePicker({name, ...rest}) {
  return (
    <FinalField
      name={name}
      component={WeekdayRecurrencePicker}
      isEqual={unsortedArraysEqual}
      {...rest}
    />
  );
}

FinalWeekdayRecurrencePicker.propTypes = {
  name: PropTypes.string.isRequired,
};
