// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {Button} from 'semantic-ui-react';

export function WeekdayRecurrencePicker({onSelect, disabled, weekdays}) {
  const [selectedDays, setSelectedDays] = useState({});
  let delayTimeout = null;

  useEffect(() => {
    return () => {
      if (delayTimeout) {
        clearTimeout(delayTimeout);
      }
    };
  }, [delayTimeout]);

  const preselectWeekdayToday = () => {
    const weekdayToday = moment()
      .locale('en')
      .format('ddd')
      .toLowerCase();

    setSelectedDays(prevSelectedDays => ({
      ...prevSelectedDays,
      [weekdayToday]: true,
    }));
  };

  useEffect(() => {
    if (!weekdays || weekdays.length === 0) {
      preselectWeekdayToday();
    } else {
      setSelectedDays(weekdays);
    }
  }, [weekdays]);

  const handleDayClick = day => {
    if (!disabled) {
      setSelectedDays(prevSelectedDays => {
        const newSelectedDays = {...prevSelectedDays};
        if (newSelectedDays[day]) {
          delete newSelectedDays[day];
        } else {
          newSelectedDays[day] = true;
        }
        return newSelectedDays;
      });

      clearTimeout(delayTimeout);
    }
  };

  useEffect(() => {
    onSelect(selectedDays);
  }, [selectedDays, onSelect]);

  const validateSelectedDays = () => {
    if (Object.keys(selectedDays).length === 0) {
      clearTimeout(delayTimeout);
      delayTimeout = setTimeout(() => {
        preselectWeekdayToday();
      }, 250);
    } else {
      clearTimeout(delayTimeout);
    }
  };

  useEffect(() => {
    validateSelectedDays();
  });

  const WEEKDAYS = moment.weekdays(true).map(weekday => ({
    value: moment()
      .day(weekday)
      .locale('en')
      .format('ddd')
      .toLowerCase(),
    text: moment()
      .isoWeekday(weekday)
      .format('ddd'),
  }));

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
            primary={selectedDays[weekday.value]}
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
  onSelect: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  weekdays: PropTypes.object,
};

WeekdayRecurrencePicker.defaultProps = {
  disabled: false,
  weekdays: {},
};

export default WeekdayRecurrencePicker;
