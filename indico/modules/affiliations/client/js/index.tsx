// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import AffiliationsDashboard from './AffiliationsDashboard';

customElements.define(
  'ind-affiliations-dashboard',
  class extends HTMLElement {
    connectedCallback() {
      ReactDOM.render(<AffiliationsDashboard />, this);
    }
  }
);
