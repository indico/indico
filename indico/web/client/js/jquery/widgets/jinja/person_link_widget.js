// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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
    const {
      fieldId,
      eventId,
      roles,
      sessionUser,
      hasPredefinedAffiliations,
      allowCustomAffiliations,
      customPersonsMode,
      requiredPersonFields,
      defaultSearchExternal,
      nameFormat,
      extraParams,
      ...rest
    } = options;
    const field = document.getElementById(fieldId);
    const persons = JSON.parse(field.value);
    const user = sessionUser &&
      sessionUser.id !== undefined && {
        title: sessionUser.title,
        userId: sessionUser.id,
        userIdentifier: `User:${sessionUser.id}`,
        avatarURL: sessionUser.avatarURL,
        firstName: sessionUser.firstName,
        lastName: sessionUser.lastName,
        affiliation: sessionUser.affiliation,
        affiliationId: sessionUser.affiliationId,
        affiliationMeta: sessionUser.affiliationMeta,
        email: sessionUser.email,
        address: sessionUser.address,
        phone: sessionUser.phone,
        type: sessionUser.type,
      };

    ReactDOM.render(
      <WTFPersonLinkField
        fieldId={fieldId}
        eventId={eventId}
        defaultValue={camelizeKeys(persons)}
        roles={roles || []}
        sessionUser={user}
        hasPredefinedAffiliations={hasPredefinedAffiliations}
        allowCustomAffiliations={allowCustomAffiliations}
        customPersonsMode={customPersonsMode}
        requiredPersonFields={requiredPersonFields}
        defaultSearchExternal={defaultSearchExternal}
        nameFormat={nameFormat}
        extraParams={camelizeKeys(extraParams)}
        {...rest}
      />,
      document.getElementById(`person-link-field-${fieldId}`)
    );
  };
})(window);
