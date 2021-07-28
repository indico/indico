// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {WTFPrincipalListField} from 'indico/react/components';

window.setupPrincipalListWidget = function setupPrincipalListWidget({fieldId, eventId, ...options}) {
  options = {
    ...{
      withGroups: false,
      withExternalUsers: false,
      withEventRoles: false,
      withCategoryRoles: false,
      withRegistrants: false,
      withEmails: false,
    },
    ...options,
  };
  const field = document.getElementById(fieldId);
  const principals = JSON.parse(field.value);

  ReactDOM.render(
    <WTFPrincipalListField
      fieldId={fieldId}
      defaultValue={principals}
      eventId={eventId}
      {...options} />,
    document.getElementById(`userGroupList-${fieldId}`)
  );
};
