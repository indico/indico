// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-env commonjs */
/* eslint-disable import/unambiguous, import/no-commonjs */

const path = require('path');
const process = require('process');

const plugins = [
  '@babel/plugin-transform-runtime',
  '@babel/plugin-proposal-class-properties',
  [
    '@dr.pogodin/react-css-modules',
    {
      exclude: 'node_modules',
      context: 'indico/modules',
      filetypes: {
        '.scss': {
          syntax: 'postcss-scss',
        },
      },
      autoResolveMultipleImports: true,
      generateScopedName: '[path]___[name]__[local]___[hash:base64:5]',
    },
  ],
  'macros',
];

if (process.env.NODE_ENV === 'test' || process.env.MOCK_FLASK_URLS === '1') {
  plugins.push(['flask-urls', {importPrefix: 'indico-url', mock: true}]);
} else {
  // if there is a valid build config, we can use it to generate proper URLs
  try {
    const config = require(process.env.INDICO_PLUGIN_ROOT
      ? path.join(process.env.INDICO_PLUGIN_ROOT, 'webpack-build-config')
      : './webpack-build-config');
    const globalBuildConfig = config.indico ? config.indico.build : config.build;

    plugins.push([
      'flask-urls',
      {
        importPrefix: 'indico-url',
        urlMap: require(config.build.urlMapPath).rules,
        basePath: globalBuildConfig.baseURLPath,
      },
    ]);
  } catch (e) {
    if (e.code !== 'MODULE_NOT_FOUND') {
      throw e;
    }
  }
}

module.exports = {
  presets: ['@babel/preset-env', '@babel/react', '@babel/preset-typescript'],
  plugins,
};
