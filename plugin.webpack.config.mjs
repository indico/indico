// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {readFileSync} from 'node:fs';
import path from 'path';
import process from 'process';

import glob from 'glob';
import _ from 'lodash';
import {mergeWithCustomize, customizeArray} from 'webpack-merge';

const config = JSON.parse(
  readFileSync(path.join(process.env.INDICO_PLUGIN_ROOT, 'webpack-build-config.json'))
);
const bundles = JSON.parse(
  readFileSync(path.join(process.env.INDICO_PLUGIN_ROOT, 'webpack-bundles.json'))
);
const base = await import(path.join(config.build.indicoSourcePath, 'webpack/base.mjs'));

const entry = bundles.entry || {};

if (!_.isEmpty(config.themes)) {
  const themeFiles = base.getThemeEntryPoints(config, './themes/');
  Object.assign(entry, themeFiles);
}

function generateModuleAliases() {
  return glob.sync(path.join(config.indico.build.rootPath, 'modules/**/module.json')).map(file => {
    const mod = {produceBundle: true, partials: {}, ...JSON.parse(readFileSync(file))};
    const dirName = path.join(path.dirname(file), 'client/js');
    const modulePath = path.join('indico/modules', mod.parent || '', mod.name);
    return {
      name: modulePath,
      alias: dirName,
      onlyModule: false,
    };
  });
}

export default env => {
  return mergeWithCustomize({
    customizeArray: customizeArray({
      'resolve.alias': 'prepend',
    }),
  })(base.webpackDefaults(env, config, bundles, true), {
    entry,
    externals: {
      'jquery': 'jQuery',
      'moment': 'moment',
      'flask-urls': '_IndicoCoreFlaskUrls',
      'react': '_IndicoCoreReact',
      'react-dnd': '_IndicoCoreReactDnd',
      'react-dom': '_IndicoCoreReactDom',
      'react-redux': '_IndicoCoreReactRedux',
      'react-router': '_IndicoCoreReactRouter',
      'react-router-dom': '_IndicoCoreReactRouterDom',
      'prop-types': '_IndicoCorePropTypes',
      'redux': '_IndicoCoreRedux',
      'semantic-ui-react': '_IndicoCoreSUIR',
      'react-final-form': '_IndicoCoreReactFinalForm',
      'indico/react/components': '_IndicoReactComponents',
      'indico/react/components/syncedInputs': '_IndicoSyncedInputs',
      'indico/react/forms': '_IndicoReactForm',
      'indico/react/forms/fields': '_IndicoReactFormField',
      'indico/react/i18n': '_IndicoReactI18n',
      'indico/react/util': '_IndicoReactUtil',
      'indico/utils/axios': '_IndicoUtilsAxios',
      'indico/utils/date': '_IndicoUtilsDate',
      'indico/utils/case': '_IndicoUtilsCase',
      'indico/utils/plugins': '_IndicoUtilsPlugins',
      'indico/react/components/principals/imperative': '_IndicoPrincipalsImperative',
      'indico/custom_elements': '_IndicoCustomElements',
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
