// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import AffiliationsDashboard from './AffiliationsDashboard';

const ROOT_ELEMENT_ID = 'affiliations-dashboard-root';

function renderAffiliationsDashboard(): void {
  const container = document.getElementById(ROOT_ELEMENT_ID);

  if (!container) {
    return;
  }

  ReactDOM.render(<AffiliationsDashboard />, container);
}

declare global {
  interface Window {
    setupAffiliationsDashboards: () => void;
  }
}

window.setupAffiliationsDashboards = function setupAffiliationsDashboards(): void {
  renderAffiliationsDashboard();
};
