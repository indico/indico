/* eslint-env commonjs */
/* eslint-disable import/unambiguous, import/no-commonjs */

const plugins = [
  '@babel/plugin-transform-runtime',
  '@babel/plugin-proposal-class-properties',
  'lodash',
  [
    'react-css-modules',
    {
      exclude: 'node_modules',
      context: 'indico/modules',
      filetypes: {
        '.scss': {
          syntax: 'postcss-scss',
        },
      },
      autoResolveMultipleImports: true,
    },
  ],
  'macros',
];

// if there is a valid build config, we can use it to generate proper URLs
try {
  const config = require('./webpack-build-config');
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

module.exports = {
  presets: ['@babel/preset-env', '@babel/react'],
  plugins,
};
