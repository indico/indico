// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import TemplateManagement from './TemplateManagement';

window.setupReceiptTemplateList = function(
  elem,
  ownTemplates,
  inheritedTemplates,
  otherTemplates,
  defaultTemplates,
  targetLocator
) {
  document.addEventListener('DOMContentLoaded', () => {
    ReactDOM.render(
      <TemplateManagement
        initialState={{ownTemplates, inheritedTemplates, otherTemplates}}
        defaultTemplates={defaultTemplates}
        targetLocator={targetLocator}
      />,
      elem
    );
  });
};
