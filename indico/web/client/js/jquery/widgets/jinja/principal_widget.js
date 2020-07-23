// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {WTFPrincipalField} from 'indico/react/components';

window.setupPrincipalWidget = function setupPrincipalWidget({
  fieldId,
  required,
  withExternalUsers,
}) {
  const field = document.getElementById(fieldId);

  ReactDOM.render(
    <WTFPrincipalField
      fieldId={fieldId}
      defaultValue={field.value}
      required={required}
      withExternalUsers={withExternalUsers}
    />,
    document.getElementById(`principalField-${fieldId}`)
  );
};
