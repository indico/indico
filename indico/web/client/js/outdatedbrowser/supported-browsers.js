// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// XXX: This script runs at build time. It is not transpiled so it can
// only use features natively support by NodeJS!

/* eslint-disable import/no-commonjs, import/unambiguous */
/* global module:false, __dirname:false */

const path = require('path');

const browserslist = require('browserslist');
const semver = require('semver');
const BROWSERSLIST_PATH = path.join(__dirname, '..', '..', '..', '..', '..', '.browserslistrc');

const browsers = browserslist(null, {
  env: 'production',
  config: BROWSERSLIST_PATH,
}).reduce((accum, text) => {
  // get only the lowest version of a browser
  const parts = text.split(' ');
  const browser = parts[0];
  let version = parts[1];

  // version ranges - take the lowest
  if (version.includes('-')) {
    version = version.split('-')[0];
  }
  if (accum[browser]) {
    if (semver.gt(semver.coerce(version), semver.coerce(accum[browser]))) {
      // found a higher version, ignore it
      return accum;
    }
  }
  accum[browser] = version;
  return accum;
}, {});

const convert = version => {
  const [, major, minor] = version.match(/^(\d+)(?:\.(\d+))?$/);
  if (minor === undefined) {
    return +major;
  } else {
    return {major: +major, minor: +minor};
  }
};

const mapped = {
  Chrome: convert(browsers.chrome),
  Edge: convert(browsers.edge),
  Safari: convert(browsers.safari),
  'Mobile Safari': convert(browsers.ios_saf),
  Firefox: convert(browsers.firefox),
  IE: false,
};

module.exports = mapped;
