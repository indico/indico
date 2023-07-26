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

function WeekdayRecurrencePicker({onSelect}) {
  const [selectedDays, setSelectedDays] = useState({});
  let delayTimeout = null;

  useEffect(() => {
    return () => {
      if (delayTimeout) {
        clearTimeout(delayTimeout);
      }
    };
  }, [delayTimeout]);

  const preselectFirstWeekday = () => {
    const firstWeekday = moment()
      .weekday(0)
      .locale('en')
      .format('ddd')
      .toLowerCase();

    setSelectedDays(prevSelectedDays => ({
      ...prevSelectedDays,
      [firstWeekday]: true,
    }));
  };

  useEffect(() => {
    preselectFirstWeekday();
  }, []);

  const handleDayClick = day => {
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
  };

  useEffect(() => {
    onSelect(selectedDays);
  }, [selectedDays, onSelect]);

  const validateSelectedDays = () => {
    if (Object.keys(selectedDays).length === 0) {
      clearTimeout(delayTimeout);
      delayTimeout = setTimeout(() => {
        preselectFirstWeekday();
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
            key={weekday.value}
            value={weekday.value}
            compact
            className={selectedDays[weekday.value] ? 'primary' : ''}
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
};

export default WeekdayRecurrencePicker;
