// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import SessionForm from './components/SessionForm';

(function(global) {
  global.setupTimetable = function setupTimetable() {
    const root = document.querySelector('#timetable-container');
    if (root) {
      ReactDOM.render(<SessionForm />, root);
    }
  };
})(window);
