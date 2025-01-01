// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {WTFDurationField} from 'indico/react/components';

window.setupDurationWidget = function setupDurationWidget({fieldId, required, disabled}) {
  // Make sure the results dropdown is displayed above the dialog.
  const field = $(`#${fieldId}`);
  field.closest('.ui-dialog-content').css('overflow', 'inherit');
  field.closest('.exclusivePopup').css('overflow', 'inherit');

  ReactDOM.render(
    <WTFDurationField
      timeId={`${fieldId}-timestorage`}
      required={required}
      disabled={disabled}
    />,
    document.getElementById(fieldId)
  );
};
