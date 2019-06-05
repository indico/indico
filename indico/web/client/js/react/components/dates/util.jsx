// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import {VERTICAL_ORIENTATION} from 'react-dates/constants';
import Responsive from 'react-responsive';

/**
 * This is a HOC that sets a full-screen layout when the screen is too small.
 * It will work with both `react-date`'s `RangePicker`  and `SinglePicker`.
 */
export const responsiveReactDates = (Component, props) => {
  const verticalLayout = (
    <Component {...props} withFullScreenPortal orientation={VERTICAL_ORIENTATION} />
  );

  return (
    <>
      <Responsive minWidth={600} minHeight={700}>
        <Component {...props} />
      </Responsive>
      {/* Small screens, Portrait */}
      <Responsive maxWidth={599} maxHeight={699}>
        {verticalLayout}
      </Responsive>
      {/* Landscape */}
      <Responsive minWidth={600} maxHeight={699}>
        <Component {...props} withFullScreenPortal />
      </Responsive>
      {/* Portrait */}
      <Responsive maxWidth={599} minHeight={699}>
        {verticalLayout}
      </Responsive>
    </>
  );
};
