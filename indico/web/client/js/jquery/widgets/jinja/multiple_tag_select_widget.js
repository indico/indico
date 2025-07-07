// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {WTFMultipleTagSelectField} from 'indico/react/components';

window.setupMultipleTagSelectWidget = function setupMultipleTagSelectWidget({
  fieldId,
  choices,
  inputArgs,
  initialSelection,
}) {
  const wrapperId = `${fieldId}-wrapper`;
  // The form dialog has a combination of overflow: hidden and auto.
  // Since WTFMultipleTagSelectField is much larger when expanded, most of its
  // options would not be visible without changing the overflow property to visible.
  const popup = $(`#${wrapperId}`).closest('.exclusivePopup');
  const dialog = popup.parent();
  popup.css('overflow', 'visible');
  dialog.css('overflow', 'visible');

  ReactDOM.render(
    <WTFMultipleTagSelectField
      fieldId={fieldId}
      choices={choices}
      inputArgs={inputArgs}
      initialSelection={initialSelection}
    />,
    document.getElementById(wrapperId)
  );
};
