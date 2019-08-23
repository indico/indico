// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import SearchApp from './components/SearchApp';
import SearchBar from './components/SearchBar';

document.addEventListener('DOMContentLoaded', () => {
  const bar = document.querySelector('#search-bar');
  ReactDOM.render(<SearchBar />, bar);
});

document.addEventListener('DOMContentLoaded', () => {
  const root = document.querySelector('#search-root');
  ReactDOM.render(<SearchApp />, root);
});

/*
TODOS:
search form when press the /search and then redirect you to the result page, can be simple fields form,
in path make li items and after element renders the >>
pagination
ask about occassional rendering of other things as well
*/
