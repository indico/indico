// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

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
