// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {WTFPrincipalListField} from 'indico/react/components';

window.setupPrincipalListWidget = function setupPrincipalListWidget({fieldId, ...options}) {
  options = {
    ...{
      eventId: null,
      withGroups: false,
      withExternalUsers: false,
      withEventRoles: false,
      withCategoryRoles: false,
      withRegistrants: false,
      withEmails: false,
      searchToken: null,
    },
    ...options,
  };
  const field = document.getElementById(fieldId);
  const principals = JSON.parse(field.value);

  ReactDOM.render(
    <WTFPrincipalListField fieldId={fieldId} defaultValue={principals} {...options} />,
    document.getElementById(`userGroupList-${fieldId}`)
  );
};
