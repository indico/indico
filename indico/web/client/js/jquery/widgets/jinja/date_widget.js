// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {WTFDateField} from 'indico/react/components';

window.setupDateWidget = function setupDateWidget(options) {
  options = $.extend(
    true,
    {
      fieldId: null,
      required: false,
      disabled: false,
      allowClear: false,
      earliest: null,
      latest: null,
      linkedField: {
        id: null,
        notBefore: false,
        notAfter: false,
      },
      weekendDisabled: false,
      disabledDates: null
    },
    options
  );

  // Make sure the results dropdown are displayed above the dialog.
  const field = $(`#${options.fieldId}`);
  field.closest('.ui-dialog-content').css('overflow', 'inherit');
  field.closest('.exclusivePopup').css('overflow', 'inherit');

  ReactDOM.render(
    <WTFDateField
      dateId={`${options.fieldId}-datestorage`}
      required={options.required}
      disabled={options.disabled}
      allowClear={options.allowClear}
      earliest={options.earliest}
      latest={options.latest}
      linkedField={options.linkedField}
      weekendDisabled={options.weekendDisabled}
      disabledDates={options.disabledDates}
    />,
    document.getElementById(options.fieldId)
  );
};
