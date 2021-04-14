// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'core-js/es6';

import './legacy/presentation.js';
import './legacy/indico.js';
import './legacy/timetable.js';

import '../styles/screen.scss';
import 'indico-sui-theme/semantic.css';
import 'rc-time-picker/assets/index.css';
import 'react-dates/lib/css/_datepicker.css';

import showReactErrorDialog from 'indico/react/errors';

// XXX: some plugins (and legacy code) use it
window.showErrorDialog = (error, instantReport = false) => {
  if (process.env.NODE_ENV === 'development') {
    console.warn('Legacy showErrorDialog called');
  }
  return showReactErrorDialog(error, instantReport);
};
