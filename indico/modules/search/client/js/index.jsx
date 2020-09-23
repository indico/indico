// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {BrowserRouter as Router, Route} from 'react-router-dom';
import {QueryParamProvider} from 'use-query-params';
import SearchApp from './components/SearchApp';

document.addEventListener('DOMContentLoaded', () => {
  const root = document.querySelector('#search-root');
  ReactDOM.render(
    <Router>
      <QueryParamProvider ReactRouterRoute={Route}>
        <SearchApp />
      </QueryParamProvider>
    </Router>,
    root
  );
});
