// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {WTFPrivacyPolicyURLsField} from 'indico/react/components';

window.setupPrivacyPolicyURLsWidget = function setupPrivacyPolicyURLsWidget({
  fieldId,
  initialValues,
}) {
  const wrapperId = `${fieldId}-wrapper`;
  ReactDOM.render(
    <WTFPrivacyPolicyURLsField fieldId={fieldId} wrapperId={wrapperId} initialValues={initialValues} />,
    document.getElementById(wrapperId)
  );
};
