// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
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
  const id = parseInt(root.dataset.id, 10) || undefined;
  const title = root.dataset.title;

  ReactDOM.render(
    <Router>
      <SearchApp category={{id, title}} />
    </Router>,
    root
  );
});
