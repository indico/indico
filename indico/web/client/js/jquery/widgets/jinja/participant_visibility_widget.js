// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {WTFParticipantVisibilityField} from 'indico/react/components';

window.setupParticipantVisibilityWidget = function setupParticipantVisibilityWidget({
  fieldId,
  values,
  choices,
  maxVisibilityPeriod,
}) {
  const wrapperId = `${fieldId}-wrapper`;
  ReactDOM.render(
    <WTFParticipantVisibilityField
      fieldId={fieldId}
      wrapperId={wrapperId}
      values={values}
      choices={choices}
      maxVisibilityPeriod={maxVisibilityPeriod}
    />,
    document.getElementById(wrapperId)
  );
};
