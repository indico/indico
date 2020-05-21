// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import path from 'path';
import glob from 'glob';
import merge from 'webpack-merge';
import CopyWebpackPlugin from 'copy-webpack-plugin';
import {minify} from 'uglify-js';
import webpack from 'webpack';

import {
  getThemeEntryPoints,
  webpackDefaults,
  indicoStaticLoader,
  generateAssetPath,
} from './webpack';
import config from './webpack-build-config';

let entryPoints = {
  jquery: ['./js/jquery/index.js'],
  main: ['./js/index.js'],
  ckeditor: ['./js/jquery/ckeditor.js'],
  conferences: ['./styles/legacy/Conf_Basic.scss'],
  markdown: ['./js/jquery/markdown.js'],
  mathjax: ['./js/jquery/compat/mathjax.js'],
  statistics: ['./js/jquery/statistics.js'],
  fonts: ['./styles/partials/_fonts.scss'],
  outdatedbrowser: ['./js/outdatedbrowser/index.js'],
};

const modulesDir = path.join(config.build.rootPath, '..', 'node_modules');
const extraResolveAliases = [
  {name: 'jquery', alias: path.resolve(modulesDir, 'jquery/src/jquery')},
];

// Add Module Bundles
glob.sync(path.join(config.build.rootPath, 'modules/**/module.json')).forEach(file => {
  const module = {produceBundle: true, partials: {}, ...require(file)};
  // eslint-disable-next-line prefer-template
  const moduleName = 'module_' + (module.parent ? module.parent + '.' : '') + module.name;
  const dirName = path.join(path.dirname(file), 'client/js');

  if (module.produceBundle) {
    entryPoints[moduleName] = [dirName];
  }
  const modulePath = path.join('indico/modules', module.parent || '', module.name);
  extraResolveAliases.push({name: modulePath, alias: dirName, onlyModule: false});

  if (module.partials) {
    for (const partial of Object.entries(module.partials)) {
      entryPoints[`${moduleName}.${partial[0]}`] = [path.resolve(dirName, partial[1])];
    }
  }
});

// This has to be last in the array, since it's the most general alias.
// Otherwise, it would be caught before 'indico/modules/...'
extraResolveAliases.push({
  name: 'indico',
  alias: path.join(config.build.clientPath, 'js/'),
  onlyModule: false,
});

// Add Meeting Themes
entryPoints = Object.assign(entryPoints, getThemeEntryPoints(config, './themes/'));

export default env => {
  const currentEnv = (env ? env.NODE_ENV : null) || 'development';

  // Minification of copied files (e.g. CKEditor and MathJax)
  const transform =
    currentEnv === 'development'
      ? undefined
      : (content, filePath) => {
          if (!filePath.match(/\.js$/)) {
            return content;
          }
          const result = minify(content.toString());
          if (result.error) {
            throw result.error;
          }
          return result.code;
        };

  return merge.strategy({
    // resolve module aliases first, since the ones
    // in base.js are more general
    'resolve.alias': 'prepend',
  })(webpackDefaults(env, config), {
    entry: entryPoints,
    module: {
      rules: [
        {
          test: /client\/js\/legacy\/libs\/.*$/,
          use: 'script-loader',
        },
        {
          test: /\.tpl\.html$/,
          use: {
            loader: 'file-loader',
            options: {
              name: '[path][name].[ext]',
              context: config.build.distPath,
              outputPath: 'mod_assets/',
            },
          },
        },
        {
          include: /jquery-migrate/,
          parser: {
            amd: false,
          },
        },
        indicoStaticLoader(config),
        {
          test: /\/node_modules\/.*\.(jpe?g|png|gif|svg|woff2?|ttf|eot)$/,
          use: {
            loader: 'file-loader',
            options: {
              name: generateAssetPath(config),
              context: config.build.distPath,
              outputPath: 'mod_assets/',
              publicPath: `${config.build.distURL}mod_assets/`,
            },
          },
        },
      ],
    },
    plugins: [
      new CopyWebpackPlugin([
        {
          from: path.resolve(modulesDir, 'ckeditor/dev/builder/release/ckeditor'),
          to: 'js/ckeditor',
          transform,
        },
        {from: path.resolve(modulesDir, 'mathjax'), to: 'js/mathjax', transform},
      ]),
      new webpack.ProvidePlugin({
        _: ['underscore', 'default'],
        moment: 'moment',
      }),
    ],
    resolve: {
      alias: extraResolveAliases,
    },
    output: {
      jsonpFunction: 'coreJsonp',
    },
  });
};
