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

const config = require('./config');
const path = require('path');
const webpack = require('webpack')
const CopyWebpackPlugin = require('copy-webpack-plugin');
const ExtractTextPlugin = require('extract-text-webpack-plugin')
const ManifestPlugin = require('webpack-manifest-plugin');
const glob = require('glob');
const uglify = require('uglify-js');

const clientDir = path.join(__dirname, 'indico', 'web', 'client');
const modulesDir = path.join(__dirname, 'node_modules');

const _cssLoaderOptions = {
    root: config.build.staticPath,
    sourceMap: true
};

const entryPoints = {
    main: './js/index.js',
    ckeditor: './js/jquery/ckeditor.js',
    conferences: './styles/legacy/Conf_Basic.css',
    map_of_rooms: './styles/legacy/mapofrooms.css',
    markdown: './js/jquery/markdown.js',
    mathjax: './js/jquery/compat/mathjax.js',
    statistics: './js/jquery/statistics.js',
    fonts: './styles/partials/_fonts.scss'
};

const resolveAlias = [
    {name: 'jquery', alias: 'jquery/src/jquery', onlyModule: false}
];

// Add Module Bundles
glob.sync(path.join(__dirname, 'indico/modules/**/module.json')).forEach((file) => {
    const module = Object.assign({produceBundle: true, partials: {}}, require(file));
    const moduleName = 'module_' + (module.parent ? (module.parent + '.') : '') + module.name;
    const dirName = path.join(path.dirname(file), 'js');

    if (module.produceBundle) {
        entryPoints[moduleName] = dirName;
    }
    const modulePath = 'indico/modules/' + (module.parent ? (module.parent + '/') : '') + module.name;
    resolveAlias.push({name: modulePath, alias: dirName, onlyModule: false});

    if (module.partials) {
        for (const partial of Object.entries(module.partials)) {
            entryPoints[moduleName + '.' + partial[0]] = path.resolve(dirName, partial[1]);
        }
    }
});

// This has to be last in the array, since it's the most general alias.
// Otherwise, it would be caught before 'indico/modules/...'
resolveAlias.push({name: 'indico', alias: path.join(clientDir, 'js/'), onlyModule: false});

// Add Meeting Themes
Object.assign(entryPoints, ...Object.keys(config.themes).map((k) => {
    const returnValue = {};
    const prefix = './styles/themes/';
    const escapedKey = k.replace('-', '_');

    returnValue['themes_' + escapedKey] = prefix + config.themes[k].stylesheet;
    if (config.themes[k].print_stylesheet) {
        returnValue['themes_' + escapedKey + '.print'] = prefix + config.themes[k].print_stylesheet;
    }
    return returnValue;
}));

module.exports = env => {
    const currentEnv = (env ? env.NODE_ENV : null) || 'development';

    // Minification of copied files (CKEditor and MathJax)
    const transform = currentEnv === 'development' ? null : (content, path) => {
        if (!path.match(/\.js$/)) {
            return content;
        }
        return uglify.minify(content.toString(), {fromString: true}).code;
    };

    return {
        devtool: 'source-map',
        context: clientDir,
        entry: entryPoints,
        output: {
            path: config.build.distPath,
            filename: "js/[name].bundle.js",
            publicPath: config.build.distURL
        },
        module: {
            rules: [
                {
                    test: /\.js$/,
                    use: 'babel-loader',
                    exclude: /node_modules/
                },
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
                {
                    test: /\.css$/,
                    use: ExtractTextPlugin.extract({
                        fallback: 'style-loader',
                        use: {
                            loader: 'css-loader',
                            options: _cssLoaderOptions
                        }
                    })
                },
                {
                    test: /\.scss$/,
                    use: ExtractTextPlugin.extract({
                        fallback: 'style-loader',
                        use: [{
                            loader: 'css-loader',
                            options: _cssLoaderOptions
                        }, {
                            loader: 'sass-loader',
                            options: {
                                sourceMap: currentEnv === 'development',
                                includePaths: [path.join(clientDir, 'styles')]
                            }
                        }, 'postcss-loader'],
                    })
                },
                {
                    test: /\/static\/(images|fonts)\/.*\.(jpe?g|png|gif|svg|woff2?|ttf|svg|eot)$/,
                    use: {
                        loader: 'file-loader',
                        options: {
                            name: '[path][name].[ext]',
                            context: config.build.staticPath,
                            emitFile: false
                        }
                    }
                },
                {
                    test: /\/node_modules\/.*\.(jpe?g|png|gif|svg|woff2?|ttf|svg|eot)$/,
                    use: {
                        loader: 'file-loader',
                        options: {
                            name: '[path][name].[ext]',
                            context: config.build.distPath,
                            outputPath: 'mod_assets/'
                        }
                    }
                }
            ]
        },
        plugins: [
            new ManifestPlugin({
                fileName: 'manifest.json',
                publicPath: config.build.distURL
            }),
            new webpack.ProvidePlugin({
                $: 'jquery',
                jQuery: 'jquery',
                _: 'underscore',
                moment: 'moment'
            }),
            new webpack.optimize.CommonsChunkPlugin({
                name: 'common' // Specify the common bundle's name.
            }),
            // Do not load moment locales (we'll load them explicitly)
            new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),
            new ExtractTextPlugin({
                filename: 'css/[name].css'
            }),
            new webpack.EnvironmentPlugin({
                NODE_ENV: currentEnv
            }),
            new CopyWebpackPlugin([
                {from: path.resolve(modulesDir, 'ckeditor/dev/builder/release/ckeditor'), to: 'js/ckeditor', transform},
                {from: path.resolve(modulesDir, 'mathjax'), to: 'js/mathjax', transform}
            ])
        ],
        resolve: {
            alias: resolveAlias
        }
    };
};
