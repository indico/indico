// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {BrowserRouter as Router} from 'react-router-dom';

import SearchApp from './components/SearchApp';

document.addEventListener('DOMContentLoaded', () => {
  const root = document.querySelector('#search-root');

  if (root) {
    const category = root.dataset.category ? JSON.parse(root.dataset.category) : null;
    const eventId = root.dataset.eventId !== undefined ? parseInt(root.dataset.eventId, 10) : null;
    const isAdmin = root.dataset.isAdmin !== undefined;

    ReactDOM.render(
      <Router>
        <SearchApp category={category} eventId={eventId} isAdmin={isAdmin} />
      </Router>,
      root
    );
  }
});
