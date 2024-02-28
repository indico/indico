// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import Timetable from './Timetable';

import 'react-big-calendar/lib/css/react-big-calendar.css';

(function(global) {
  global.setupNewTimetable = function setupNewTimetable() {
    const timetableContainer = document.querySelector('#timetable-container');
    if (timetableContainer) {
      ReactDOM.render(<Timetable />, timetableContainer);
    }
  };
})(window);
