// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import preval from 'preval.macro';

import outdatedBrowser from './outdatedbrowser';
import './outdatedbrowser.css';

// get list of supported browsers at build time
const browserSupport = preval`
  module.exports = require('./supported-browsers');
`;

outdatedBrowser({
  browserSupport,
  messages: {
    updateOutdated: {
      web:
        'Indico may not work correctly in this browser.<br><br>' +
        'Please use the latest version of Firefox, Chrome or Edge.',
      googlePlay: 'Please install Chrome or Firefox from Google Play',
      appStore: 'Please update iOS from the Settings App',
    },
    updateUnsupported: {
      web:
        'Indico does not work correctly in this browser.<br><br>' +
        'Please use Firefox, Chrome or Edge instead.',
      googlePlay: 'Please install Chrome or Firefox from Google Play',
      appStore: 'Please update iOS from the Settings App',
    },
    unsupported: `⚠ Internet Explorer is not supported anymore ⚠`,
    outdated: '⚠ Your browser is out of date ⚠',
  },
});
