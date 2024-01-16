// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment/moment';
import PropTypes from 'prop-types';
import React from 'react';

import SingleDatePicker from './SingleDatePicker';

function renderMonthElement(threshold, {month, onMonthSelect, onYearSelect}) {
  const years = [];
  for (let i = month.year() - threshold; i <= month.year() + threshold; i++) {
    years.push(i);
  }
  return (
    <div style={{display: 'flex', justifyContent: 'center'}}>
      <select value={month.month()} onChange={e => onMonthSelect(month, e.target.value)}>
        {moment.months().map((text, value) => (
          <option key={text} value={value}>
            {text}
          </option>
        ))}
      </select>
      <select value={month.year()} onChange={e => onYearSelect(month, e.target.value)}>
        {years.map(y => (
          <option key={y} value={y}>
            {y}
          </option>
        ))}
      </select>
    </div>
  );
}

export default function CalendarYearMonthPicker({threshold, ...props}) {
  return React.createElement(SingleDatePicker, {
    ...props,
    renderMonthElement: params => renderMonthElement(threshold, params),
  });
}

CalendarYearMonthPicker.propTypes = {
  threshold: PropTypes.number,
};

CalendarYearMonthPicker.defaultProps = {
  threshold: 5,
};
