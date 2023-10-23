// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import AutoLinkerConfig from './components/AutoLinkerConfig';

window.setupAutoLinkerConfig = rootElementId => {
  const rootElement = document.getElementById(rootElementId);

  if (rootElement) {
    ReactDOM.render(<AutoLinkerConfig />, rootElement);
  }
};
