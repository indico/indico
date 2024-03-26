// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import Router from './TemplateManagement';

window.setupReceiptTemplateList = function(
  elem,
  ownTemplates,
  inheritedTemplates,
  defaultTemplates,
  targetLocator
) {
  document.addEventListener('DOMContentLoaded', () => {
    ReactDOM.render(
      <Router
        initialState={{ownTemplates, inheritedTemplates}}
        defaultTemplates={defaultTemplates}
        targetLocator={targetLocator}
      />,
      elem
    );
  });
};
