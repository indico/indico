// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';

import {Responsive} from 'indico/react/util';

export default function dateRenderer({startDate, endDate}) {
  startDate = startDate ? moment(startDate) : null;
  endDate = endDate ? moment(endDate) : null;

  if (!startDate && !endDate) {
    return null;
  } else if (!endDate) {
    return (
      <Responsive.Tablet andLarger orElse={startDate.format('D MMM')}>
        {startDate.format('ddd D MMM')}
      </Responsive.Tablet>
    );
  } else {
    return (
      <Responsive.Tablet
        andLarger
        orElse={`${startDate.format('D MMM')} - ${endDate.format('D MMM')}`}
      >
        {`${startDate.format('ddd D MMM')} - ${endDate.format('ddd D MMM')}`}
      </Responsive.Tablet>
    );
  }
}
