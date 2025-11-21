// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import AffiliationsDashboard from './AffiliationsDashboard';

declare global {
  interface Window {
    setupAffiliationsDashboards: () => void;
  }
}

window.setupAffiliationsDashboards = function setupAffiliationsDashboards(): void {
  const container = document.getElementById('affiliations-dashboard-container');

  if (!container) {
    return;
  }

  ReactDOM.render(<AffiliationsDashboard />, container);
};
