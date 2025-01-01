// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {WTFDateTimeField} from 'indico/react/components';
import {localeUses24HourTime} from 'indico/utils/date';

window.setupDateTimeWidget = function setupDateTimeWidget(options) {
  options = $.extend(
    true,
    {
      fieldId: null,
      timezoneFieldId: null,
      timezone: null,
      defaultTime: null,
      locale: null,
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
    },
    options
  );

  // Make sure the results dropdown are displayed above the dialog.
  const field = $(`#${options.fieldId}`);
  field.closest('.ui-dialog-content').css('overflow', 'inherit');
  field.closest('.exclusivePopup').css('overflow', 'inherit');

  ReactDOM.render(
    <WTFDateTimeField
      timeId={`${options.fieldId}-timestorage`}
      dateId={`${options.fieldId}-datestorage`}
      timezoneFieldId={options.timezoneFieldId}
      timezone={options.timezone}
      uses24HourFormat={localeUses24HourTime(options.locale.replace('_', '-'))}
      required={options.required}
      disabled={options.disabled}
      allowClear={options.allowClear}
      earliest={options.earliest}
      latest={options.latest}
      defaultTime={options.defaultTime}
      linkedField={options.linkedField}
    />,
    document.getElementById(options.fieldId)
  );
};
