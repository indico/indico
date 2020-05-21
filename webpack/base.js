// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createHash} from 'crypto';
import fs from 'fs';
import path from 'path';

import chalk from 'chalk';
import webpack from 'webpack';

import MiniCssExtractPlugin from 'mini-css-extract-plugin';
import ManifestPlugin from 'webpack-manifest-plugin';
import ProgressBarPlugin from 'progress-bar-webpack-plugin';
import importOnce from 'node-sass-import-once';
import TerserPlugin from 'terser-webpack-plugin';

class FixedMiniCssExtractPlugin extends MiniCssExtractPlugin {
  // This very awful workaround prevents a weird `<undefined>.pop()` in the plugin
  // that's caused by who-knows-what (NOT related to dynamic imports).
  // See this github issue for details:
  // https://github.com/webpack-contrib/mini-css-extract-plugin/issues/257
  renderContentAsset(compilation, chunk, modules, requestShortener) {
    const [chunkGroup] = chunk.groupsIterable;
    let rv;
    const getModuleIndex2 = chunkGroup.getModuleIndex2;
    try {
      chunkGroup.getModuleIndex2 = null;
      rv = super.renderContentAsset(compilation, chunk, modules, requestShortener);
    } finally {
      chunkGroup.getModuleIndex2 = getModuleIndex2;
    }
    return rv;
  }
}

function _resolveTheme(rootPath, indicoClientPath, filePath) {
  const indicoRelativePath = path.resolve(indicoClientPath, filePath);

  if (
    indicoClientPath &&
    !fs.existsSync(path.resolve(rootPath, filePath)) &&
    fs.existsSync(indicoRelativePath)
  ) {
    return path.resolve(indicoClientPath, filePath);
  }

  return path.resolve(rootPath, filePath);
}

export function getThemeEntryPoints(config, prefix) {
  const themes = config.themes;
  const indicoClientPath = path.join(
    config.isPlugin ? config.indico.build.clientPath : config.build.clientPath,
    'styles'
  );
  const rootPath = path.join(config.build.rootPath);

  return Object.assign(
    ...Object.keys(themes).map(k => {
      const returnValue = {};
      const escapedKey = k.replace('-', '_');

      returnValue[`themes_${escapedKey}`] = [
        _resolveTheme(rootPath, indicoClientPath, prefix + themes[k].stylesheet),
      ];

      if (themes[k].print_stylesheet) {
        returnValue[`themes_${escapedKey}.print`] = [
          _resolveTheme(rootPath, indicoClientPath, prefix + themes[k].print_stylesheet),
        ];
      }
      return returnValue;
    })
  );
}

export function generateAssetPath(config, virtualVersion = false) {
  // /css/whatever.css => /css/whatever__v123abcdef.css
  return file => {
    const relPath = path.relative(config.build.staticPath, file);
    const {dir, name, ext} = path.parse(relPath);
    const h = createHash('md5');
    h.update(fs.readFileSync(file));
    const hash = h.digest('hex').slice(0, 8);
    // the "virtual version" is used for files that are loaded as-is from the
    // static folder and thus do not actually get the hash in the physical
    // file name. it is distinct from the normal version style so a rule on
    // the web server can strip that version segment
    const fileName = virtualVersion ? `${name}__v${hash}${ext}` : `${name}.${hash}${ext}`;
    // .. -> _, like file-loader does
    return dir.replace(/\.\./g, '_') + path.sep + fileName;
  };
}

export function webpackDefaults(env, config, bundles) {
  const globalBuildConfig = config.indico ? config.indico.build : config.build;
  const currentEnv = (env ? env.NODE_ENV : null) || 'development';
  const nodeModules = [
    path.join(
      config.build.indicoSourcePath || path.resolve(config.build.rootPath, '..'),
      'node_modules'
    ),
  ];

  if (config.isPlugin) {
    // add plugin's node_modules in addition to the core's
    nodeModules.push(path.resolve(config.build.rootPath, '../node_modules'));
  }

  const _cssLoaderOptions = {
    url: true,
  };

  const scssIncludePath = path.join(
    config.isPlugin
      ? path.resolve(config.build.indicoSourcePath, './indico/web/client')
      : path.join(config.build.clientPath),
    'styles'
  );

  function getDevtoolFilename(info) {
    const root = path.resolve(globalBuildConfig.rootPath, '..');
    return path.relative(root, info.absoluteResourcePath);
  }

  /**
   * This function resolves SASS files using a [~][module:]path syntax
   */
  function sassResolver(url) {
    const match = url.match(/^(~?)(?:(\w+):)?([\w/-_]+)/);
    if (match) {
      const skipOverride = match[1] === '~';
      const mod = match[2];
      const file = match[3];
      if (config.isPlugin) {
        const {sassOverrides} = bundles;
        if (skipOverride) {
          if (!mod) {
            return {file: path.join(config.indico.build.clientPath, 'styles', file)};
          }
        } else if (sassOverrides && sassOverrides[url]) {
          return {file: path.join(config.build.clientPath, sassOverrides[url])};
        }
      }
      if (!mod) {
        return null;
      }
      const modPath = path.join(globalBuildConfig.rootPath, 'modules', mod);
      return {file: path.join(modPath, 'client', file)};
    }
    return null;
  }

  /**
   * This function resolves url(...)s in CSS files using a plugin:path syntax
   */
  function postCSSURLResolver({url}) {
    const m = url.match(/^(\w+):(.*)$/);

    if (!m) {
      return url;
    }

    const [name, relPath] = m.slice(1);
    let prefix;

    if (name === 'static') {
      prefix = globalBuildConfig.staticURL;
    } else {
      prefix = path.join(globalBuildConfig.staticURL, 'static/plugins', name);
    }
    return path.join(prefix, relPath);
  }

  function buildSCSSLoader(cssLoaderOptions = {}) {
    return [
      {
        loader: FixedMiniCssExtractPlugin.loader,
        options: {
          publicPath: config.build.distURL,
        },
      },
      {
        loader: 'css-loader',
        options: {
          sourceMap: true,
          url: !config.isPlugin,
          ...cssLoaderOptions,
        },
      },
      {
        loader: 'resolve-url-loader',
        options: {
          keepQuery: true,
          root: config.isPlugin ? false : config.build.staticPath,
        },
      },
      {
        loader: 'postcss-loader',
        options: {
          sourceMap: true,
          config: {
            path: path.join(globalBuildConfig.rootPath, 'postcss.config.js'),
            ctx: {
              postCSSURLOptions: {
                url: postCSSURLResolver,
              },
            },
          },
        },
      },
      {
        loader: 'sass-loader',
        options: {
          sourceMap: true,
          sassOptions: {
            includePaths: [scssIncludePath],
            outputStyle: 'compact',
            importer: [sassResolver, importOnce],
          },
        },
      },
    ];
  }

  const indicoClientPath = globalBuildConfig.clientPath;

  return {
    devtool: 'source-map',
    context: config.build.clientPath,
    output: {
      path: config.build.distPath,
      filename: 'js/[name].[chunkhash:8].bundle.js',
      publicPath: config.build.distURL,
      devtoolModuleFilenameTemplate: info => `webpack:///${getDevtoolFilename(info)}`,
      devtoolFallbackModuleFilenameTemplate: info =>
        `webpack:///${getDevtoolFilename(info)}?${info.hash}`,
    },
    module: {
      rules: [
        {
          test: /outdatedbrowser\/.+\.js$/,
          loader: 'babel-loader',
          options: {
            // build JS targetting old browsers so they get the warning as well
            presets: [['@babel/preset-env', {targets: {browsers: ['last 5 years', 'ie > 6']}}]],
          },
        },
        {
          test: /\.js$/,
          loader: 'babel-loader',
          exclude: /node_modules/,
        },
        {
          test: /\.jsx$/,
          loader: 'babel-loader',
          exclude: /node_modules/,
        },
        {
          oneOf: [
            {
              test: /\.css$/,
              use: [
                {
                  loader: FixedMiniCssExtractPlugin.loader,
                },
                {
                  loader: 'css-loader',
                  options: _cssLoaderOptions,
                },
              ],
            },
            {
              test: /\.module\.scss$/,
              use: buildSCSSLoader({
                modules: {
                  context: path.resolve(globalBuildConfig.clientPath, '../../modules'),
                  localIdentName: '[path]___[name]__[local]___[hash:base64:5]',
                },
                importLoaders: 1,
              }),
            },
            {
              test: /\.scss$/,
              use: buildSCSSLoader(),
            },
          ],
        },
      ],
    },
    plugins: [
      new ManifestPlugin({
        fileName: 'manifest.json',
        publicPath: config.build.distURL,
      }),
      // Do not load moment locales (we'll load them explicitly)
      new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),
      new FixedMiniCssExtractPlugin({
        filename: 'css/[name].[contenthash:8].css',
      }),
      new ProgressBarPlugin({
        format:
          // eslint-disable-next-line prefer-template
          chalk.cyan('Code being sent to the moon and back \u{1f680} \u{1f311}') +
          '  [:bar] ' +
          chalk.green.bold(':percent') +
          ' (:elapsed seconds)',
      }),
    ],
    resolve: {
      alias: [{name: 'indico', alias: path.join(indicoClientPath, 'js/')}],
      symlinks: false,
      extensions: ['.js', '.json', '.jsx'],
      modules: nodeModules,
    },
    resolveLoader: {
      modules: nodeModules,
    },
    externals: (context, request, callback) => {
      // tell webpack to make certain packages use window.jQuery (and not load it again)
      if (/^jquery$/.test(request) && /(selectize|fullcalendar)/.test(context)) {
        return callback(null, 'jQuery');
      }
      return callback();
    },
    stats: {
      assets: false,
      children: false,
      modules: false,
      chunks: true,
      chunkModules: false,
      chunkOrigins: false,
      chunksSort: 'name',
    },
    mode: currentEnv,
    optimization: {
      splitChunks: {
        cacheGroups: {
          // 'common' chunk, which should include common dependencies
          common: {
            name: 'common',
            chunks: chunk =>
              chunk.canBeInitial() &&
              // outdatedbrowser must be fully standalone since we can assume all other
              // bundles to be broken in legacy browsers
              chunk.name !== 'outdatedbrowser' &&
              // having theme/print css in the common css bundle would break the interface
              !/\.print$|^themes_/.test(chunk.name),
            minChunks: 2,
          },
          // react/redux and friends since they are pretty big
          react: {
            test: /\/node_modules\/(react|redux|prop-types\/|lodash-es\/|fbjs\/)/,
            name: 'react',
            chunks: 'initial',
            priority: 10,
          },
          semanticui: {
            test: /node_modules\/(semantic-ui|indico-sui-theme)/,
            name: 'semantic-ui',
            chunks: 'initial',
            priority: 10,
          },
        },
      },
      minimizer: [
        new TerserPlugin({
          // XXX: minification breaks angularjs :(
          exclude: /js\/module_events\.registration\.[^.]+\.bundle\.js$/,
          extractComments: false,
          // default options from webpack
          cache: true,
          parallel: true,
          sourceMap: true,
        }),
      ],
    },
  };
}

export function indicoStaticLoader(config) {
  return {
    test: /\/static\/(images|fonts)\/.*\.(jpe?g|png|gif|svg|woff2?|ttf|eot)$/,
    use: {
      loader: 'file-loader',
      options: {
        name: generateAssetPath(config, true),
        context: config.build.staticPath,
        emitFile: false,
        publicPath: config.build.staticURL,
      },
    },
  };
}
