// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import ReactDOM from 'react-dom';
import React from 'react';
import {WTFOccurrencesField} from 'indico/react/components';
import {localeUses24HourTime} from 'indico/utils/date';

window.setupOccurrencesWidget = function setupOccurrencesWidget(options) {
  options = $.extend(
    true,
    {
      fieldId: null,
      locale: null,
    },
    options
  );

  ReactDOM.render(
    <WTFOccurrencesField
      fieldId={options.fieldId}
      uses24HourFormat={localeUses24HourTime(options.locale.replace('_', '-'))}
    />,
    document.getElementById(`${options.fieldId}-container`)
  );
};
