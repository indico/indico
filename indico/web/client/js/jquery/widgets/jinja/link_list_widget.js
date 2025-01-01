// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {WTFLinkListField} from 'indico/react/components';

window.setupLinkListWidget = function setupLinkListWidget({fieldId}) {
  const wrapperId = `${fieldId}-wrapper`;
  ReactDOM.render(
    <WTFLinkListField fieldId={fieldId} />,
    document.getElementById(wrapperId)
  );
};
