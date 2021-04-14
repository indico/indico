// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/no-commonjs, import/unambiguous, import/newline-after-import */
/* global module:false */

const path = require('path');
const process = require('process');

const glob = require('glob');
const _ = require('lodash');
const {mergeWithCustomize, customizeArray} = require('webpack-merge');

const config = require(path.join(process.env.INDICO_PLUGIN_ROOT, 'webpack-build-config'));
const bundles = require(path.join(process.env.INDICO_PLUGIN_ROOT, 'webpack-bundles'));
const base = require(path.join(config.build.indicoSourcePath, 'webpack'));

const entry = bundles.entry || {};

if (!_.isEmpty(config.themes)) {
  const themeFiles = base.getThemeEntryPoints(config, './themes/');
  Object.assign(entry, themeFiles);
}

function generateModuleAliases() {
  return glob.sync(path.join(config.indico.build.rootPath, 'modules/**/module.json')).map(file => {
    const mod = {produceBundle: true, partials: {}, ...require(file)};
    const dirName = path.join(path.dirname(file), 'client/js');
    const modulePath = path.join('indico/modules', mod.parent || '', mod.name);
    return {
      name: modulePath,
      alias: dirName,
      onlyModule: false,
    };
  });
}

module.exports = env => {
  return mergeWithCustomize({
    customizeArray: customizeArray({
      'resolve.alias': 'prepend',
    }),
  })(base.webpackDefaults(env, config, bundles, true), {
    entry,
    externals: {
      'jquery': 'jQuery',
      'react': '_IndicoCoreReact',
      'react-dom': '_IndicoCoreReactDom',
      'react-redux': '_IndicoCoreReactRedux',
      'prop-types': '_IndicoCorePropTypes',
      'redux': '_IndicoCoreRedux',
      'semantic-ui-react': '_IndicoCoreSUIR',
    },
    module: {
      rules: [
        {
          test: /.*\.(jpe?g|png|gif|svg|woff2?|ttf|eot)$/,
          use: {
            loader: 'file-loader',
          },
        },
      ],
    },
    resolve: {
      alias: generateModuleAliases(),
    },
    optimization: {
      splitChunks: {
        cacheGroups: {
          common: {
            name: 'common',
            // exclude themes/print css from common chunk
            chunks: chunk => chunk.canBeInitial() && !/\.print$|^themes_/.test(chunk.name),
            minChunks: 2,
          },
        },
      },
    },
  });
};
