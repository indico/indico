// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import preval from 'preval.macro';
import outdatedBrowser from 'outdated-browser-rework';
import 'outdated-browser-rework/dist/style.css';
import './outdatedbrowser.css';

// get list of supported browsers at build time
const browserSupport = preval`
  module.exports = require('./supported-browsers');
`;

outdatedBrowser({
  backgroundColor: '#0b63a5',
  isUnknownBrowserOK: true,
  browserSupport,
  // override language so we never get a default message
  language: 'en',
  messages: {
    en: {
      outOfDate: '⚠ Your browser is out of date ⚠',
      unsupported: `⚠ Internet Explorer is not supported anymore ⚠`,
      update: {
        web:
          'Indico may not work correctly in this browser.<br><br>' +
          'If you are using Internet Explorer, please use Firefox, Chrome or Edge instead.',
        googlePlay: 'Please install Chrome or Firefox from Google Play',
        appStore: 'Please update iOS from the Settings App',
      },
      url: null,
      close: 'Close',
    },
  },
});
