// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {WTFButtonsBooleanField} from 'indico/react/components';

window.setupButtonsBooleanWidget = function setupButtonsBooleanWidget({
  fieldId,
  trueCaption,
  falseCaption,
  disabled,
}) {
  ReactDOM.render(
    <WTFButtonsBooleanField
      checkboxId={`${fieldId}-checkbox`}
      trueCaption={trueCaption}
      falseCaption={falseCaption}
      disabled={disabled}
    />,
    document.getElementById(fieldId)
  );
};
