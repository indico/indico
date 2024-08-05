// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';

import {Translate} from 'indico/react/i18n';

const NUM_DAYS_PER_WEEK = 7;
const NUM_CALENDAR_CELLS = 42; // 6 weeks x 7 days

function DatePickerCalendarGrid({includeMonthHeader = false}) {
  return (
    <ind-date-grid data-grid>
      {includeMonthHeader ? <div className="month-label" data-month-label /> : null}
      <div className="weekdays" data-weekday-labels>
        {_.range(NUM_DAYS_PER_WEEK).map(i => (
          <abbr key={i} />
        ))}
      </div>
      <div role="listbox">
        {_.range(NUM_CALENDAR_CELLS).map(i => (
          <button type="button" role="option" key={i} />
        ))}
      </div>
    </ind-date-grid>
  );
}

DatePickerCalendarGrid.propTypes = {
  includeMonthHeader: PropTypes.bool,
};

DatePickerCalendarGrid.defaultProps = {
  includeMonthHeader: false,
};

export default function DatePickerCalendar({children}) {
  return (
    <ind-calendar>
      <dialog>
        <div className="controls">
          <button type="button" value="previous-year">
            <Translate as="span">Previous year</Translate>
          </button>
          <button type="button" value="previous-month">
            <Translate as="span">Previous month</Translate>
          </button>

          <div className="month-year">
            <select />
            <input type="number" required />
          </div>

          <button type="button" value="next-month">
            <Translate as="span">Next month</Translate>
          </button>
          <button type="button" value="next-year">
            <Translate as="span">Next year</Translate>
          </button>
        </div>

        {children}
      </dialog>
    </ind-calendar>
  );
}

DatePickerCalendar.propTypes = {
  children: PropTypes.node.isRequired,
};

DatePickerCalendar.Grid = DatePickerCalendarGrid;
