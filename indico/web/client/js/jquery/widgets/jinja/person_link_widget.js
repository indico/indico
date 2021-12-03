// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {WTFPersonLinkField} from 'indico/react/components/PersonLinkField';
import {camelizeKeys} from 'indico/utils/case';

(function(global) {
  global.setupPersonLinkWidget = function setupPersonLinkWidget(options) {
    const {fieldId, eventId, roles, sessionUser, ...rest} = options;
    const field = document.getElementById(fieldId);
    const persons = JSON.parse(field.value);

    ReactDOM.render(
      <WTFPersonLinkField
        fieldId={fieldId}
        eventId={eventId}
        defaultValue={camelizeKeys(persons)}
        roles={roles || []}
        sessionUser={
          sessionUser && {
            name: sessionUser.fullName,
            userId: sessionUser.id,
            avatarURL: sessionUser.avatarURL,
            firstName: sessionUser.firstName,
            lastName: sessionUser.lastName,
            affiliation: sessionUser.affiliation,
            email: sessionUser.email,
            address: sessionUser.address,
            phone: sessionUser.phone,
            ...sessionUser,
          }
        }
        {...rest}
      />,
      document.getElementById(`person-link-field-${fieldId}`)
    );
  };
})(window);
