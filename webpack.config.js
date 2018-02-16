/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

const path = require('path');
const glob = require('glob');

const config = require('./config');
const base = require('./webpack');

const merge = require('webpack-merge');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const uglify = require('uglify-js');
const webpack = require('webpack');

let entryPoints = {
    main: './js/index.js',
    ckeditor: './js/jquery/ckeditor.js',
    conferences: './styles/legacy/Conf_Basic.css',
    map_of_rooms: './styles/legacy/mapofrooms.css',
    markdown: './js/jquery/markdown.js',
    mathjax: './js/jquery/compat/mathjax.js',
    statistics: './js/jquery/statistics.js',
    fonts: './styles/partials/_fonts.scss'
};

const extraResolveAliases = [];
const modulesDir = path.join(config.build.rootPath, '..', 'node_modules');

// Add Module Bundles
glob.sync(path.join(config.build.rootPath, 'modules/**/module.json')).forEach((file) => {
    const module = Object.assign({produceBundle: true, partials: {}}, require(file));
    const moduleName = 'module_' + (module.parent ? (module.parent + '.') : '') + module.name;
    const dirName = path.join(path.dirname(file), 'js');

    if (module.produceBundle) {
        entryPoints[moduleName] = dirName;
    }
    const modulePath = path.join('indico/modules', module.parent || '',  module.name);
    extraResolveAliases.push({name: modulePath, alias: dirName, onlyModule: false});

    if (module.partials) {
        for (const partial of Object.entries(module.partials)) {
            entryPoints[moduleName + '.' + partial[0]] = path.resolve(dirName, partial[1]);
        }
    }
});

// This has to be last in the array, since it's the most general alias.
// Otherwise, it would be caught before 'indico/modules/...'
extraResolveAliases.push({name: 'indico', alias: path.join(config.build.clientPath, 'js/'), onlyModule: false});

// Add Meeting Themes
entryPoints = Object.assign(entryPoints, base.getThemeEntryPoints(config, './themes/'));

module.exports = env => {
    const currentEnv = (env ? env.NODE_ENV : null) || 'development';

    // Minification of copied files (e.g. CKEditor and MathJax)
    const transform = currentEnv === 'development' ? null : (content) => {
        if (!path.match(/\.js$/)) {
            return content;
        }
        return uglify.minify(content.toString(), {fromString: true}).code;
    };

    const m = merge(base.webpackDefaults(env, config), {
        entry: entryPoints,
        module: {
            rules: [
                {
                    test: /client\/js\/legacy\/libs\/.*$/,
                    use: 'script-loader'
                },
                {
                    test: /\.tpl\.html$/,
                    use: {
                        loader: 'file-loader',
                        options: {
                            name: '[path][name].[ext]',
                            context: config.build.distPath,
                            outputPath: 'mod_assets/'
                        }
                    }
                },
                {
                    include: /jquery-migrate/,
                    parser: {
                        amd: false
                    }
                },
                base.indicoStaticLoader(config),
                {
                    test: /\/node_modules\/.*\.(jpe?g|png|gif|svg|woff2?|ttf|svg|eot)$/,
                    use: {
                        loader: 'file-loader',
                        options: {
                            name: base.generateAssetPath(config),
                            context: config.build.distPath,
                            outputPath: 'mod_assets/',
                            publicPath: '/dist/'
                        }
                    }
                }
            ]
        },
        plugins: [
            new CopyWebpackPlugin([
                {from: path.resolve(modulesDir, 'ckeditor/dev/builder/release/ckeditor'), to: 'js/ckeditor', transform},
                {from: path.resolve(modulesDir, 'mathjax'), to: 'js/mathjax', transform}
            ]),
            new webpack.ProvidePlugin({
                $: 'jquery',
                jQuery: 'jquery',
                _: 'underscore',
                moment: 'moment'
            }),
            new webpack.optimize.CommonsChunkPlugin({
                name: 'common',
                minChunks: (mod, count) => {
                    if (mod.resource.match(/\/themes\/.*\.scss/)) {
                        // Let's not extract theme SCSS into the common chunk
                        // Otherwise we will have no theme SCSS files.
                        // This check is quite hacky as it relies of the file path,
                        // we should find some better way to control this threshold.
                        return false;
                    } else {
                        return count >= 3;
                    }
                }
            })
        ],
        resolve: {
            alias: extraResolveAliases
        }
    });

    return m;
};
