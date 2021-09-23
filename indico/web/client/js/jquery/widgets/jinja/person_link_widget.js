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
    const field = document.getElementById(options.fieldId);
    const persons = JSON.parse(field.value);

    ReactDOM.render(
      <WTFPersonLinkField
        fieldId={options.fieldId}
        eventId={options.eventId}
        defaultValue={camelizeKeys(persons)}
        {...options}
      />,
      document.getElementById(`person-link-field-${options.fieldId}`)
    );
  };
})(window);
