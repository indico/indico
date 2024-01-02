// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {WTFRemoteSearchDropdown} from 'indico/react/components';

window.setupRemoteSearchDropdownWidget = function setupRemoteSearchDropdownWidget(props) {
  // Make sure the dropdown is displayed above the dialog
  const field = $(`#${props.fieldId}`);
  field.closest('.ui-dialog-content').css('overflow', 'inherit');
  field.closest('.exclusivePopup').css('overflow', 'inherit');

  ReactDOM.render(<WTFRemoteSearchDropdown fieldId={props.fieldId} {...props} />, field[0]);
};
