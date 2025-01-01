// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';
import {VERTICAL_ORIENTATION, HORIZONTAL_ORIENTATION} from 'react-dates/constants';

import {Responsive} from 'indico/react/util';

/**
 * This is a HOC that sets a full-screen layout when the screen is too small.
 * It will work with both `react-date`'s `RangePicker`  and `SinglePicker`.
 */
export const responsiveReactDates = (Component, props) => {
  const supportsFullScreenPortal = 'withFullScreenPortal' in Component.defaultProps;
  const verticalLayout = (
    <Component
      {...props}
      {...(supportsFullScreenPortal ? {withFullScreenPortal: true} : {})}
      orientation={VERTICAL_ORIENTATION}
    />
  );
  const horizontalLayout = (
    <Component
      {...props}
      {...(supportsFullScreenPortal ? {withFullScreenPortal: true} : {})}
      orientation={HORIZONTAL_ORIENTATION}
    />
  );
  const component = <Component {...props} />;

  return (
    <Responsive.Tablet andSmaller orElse={component}>
      <Responsive orientation="portrait">{verticalLayout}</Responsive>
      <Responsive orientation="landscape">{horizontalLayout}</Responsive>
    </Responsive.Tablet>
  );
};

export const renderMonthElement = (
  yearsBefore,
  yearsAfter,
  {month, onMonthSelect, onYearSelect}
) => {
  const years = [];
  for (let i = month.year() - yearsBefore; i <= month.year() + yearsAfter; i++) {
    years.push(i);
  }
  return (
    <div className="datepicker-container">
      <select
        className="datepicker-select"
        value={month.month()}
        onChange={e => onMonthSelect(month, e.target.value)}
        style={{marginRight: 2}}
      >
        {moment.months().map((text, value) => (
          <option key={text} value={value}>
            {text}
          </option>
        ))}
      </select>
      <select
        className="datepicker-select"
        value={month.year()}
        onChange={e => onYearSelect(month, e.target.value)}
        style={{marginLeft: 2}}
      >
        {years.map(y => (
          <option key={y} value={y}>
            {y}
          </option>
        ))}
      </select>
    </div>
  );
};
