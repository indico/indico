// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-env commonjs */
/* eslint-disable import/unambiguous, import/no-commonjs */

// When you get an error during `npm test` that's related to ES modules, list the package
// causing it in here; this makes sure jest applies babel transforms to those modules so
// it doesn't choke on (unsupported) `export` statements
const esModules = [
  'geodesy',
  'semantic-ui-react',
  'uuid',
  'nanoid',
  'react-markdown',
  'vfile',
  'unist-.+',
  'unified',
  'bail',
  'is-plain-obj',
  'trough',
  'remark-.+',
  'mdast-util-.+',
  'micromark',
  'parse-entities',
  'character-entities',
  'property-information',
  'comma-separated-tokens',
  'hast-util-whitespace',
  'remark-.+',
  'space-separated-tokens',
  'decode-named-character-reference',
  'ccount',
  'escape-string-regexp',
  'markdown-table',
  'trim-lines',
  'axios',
].join('|');

module.exports = {
  transformIgnorePatterns: [`/node_modules/(?!${esModules})`],
  moduleNameMapper: {
    '^.+\\.(s?css)$': 'identity-obj-proxy',
    '^indico/modules/events/(reviewing|util)/(.*)$':
      '<rootDir>/indico/modules/events/client/js/$1/$2',
    '^indico/modules/events/([\\w]+)/(.*)$': '<rootDir>/indico/modules/events/$1/client/js/$2',
    '^indico/modules/([\\w]+)/(.*)$': '<rootDir>/indico/modules/$1/client/js/$2',
    '^indico/(.*)$': '<rootDir>/indico/web/client/js/$1',
  },
  setupFilesAfterEnv: ['<rootDir>/setupTests.js'],
  globals: {
    Indico: {
      Urls: {
        BasePath: '',
      },
    },
    REACT_TRANSLATIONS: {
      indico: {
        '': {
          domain: 'indico',
          lang: 'en_GB',
        },
      },
    },
    TRANSLATIONS: {
      indico: {
        '': {
          domain: 'indico',
          lang: 'en_GB',
        },
      },
    },
  },
  testEnvironment: 'jsdom',
};
