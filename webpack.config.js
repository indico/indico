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

const modulesDir = path.join(__dirname, 'node_modules');

module.exports = env => ({
    devtool: 'source-map',
    context: __dirname + "/indico/web/client",
    entry: {
        main: './js/index.js',
        markdown: './js/jquery/markdown.js',
        mathjax: './js/jquery/compat/mathjax.js',
        statistics: './js/jquery/statistics.js',
        modules_abstracts: './js/jquery/modules/abstracts.js',
        modules_rb: './js/legacy/room_booking.js',
        modules_surveys: './js/jquery/modules/surveys.js',
        modules_vc: './js/jquery/modules/vc.js'
    },
    output: {
        path: config.build.webpackPath,
        filename: "[name].bundle.js",
        publicPath: config.build.webpackURL
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
                        options: {
                            alias: {
                                '../images': config.build.imagePath
                            }
                        }
                    }
                })
            },
            {
                test: /\.(jpe?g|png|gif|svg)$/,
                use: {
                    loader: 'file-loader',
                    options: {
                        name: config.build.staticURL + '[name].[ext]'
                    }
                }
            }
        ]
    },
    plugins: [
        new ManifestPlugin({
            fileName: 'manifest.json',
            stripSrc: true,
            publicPath: config.build.webpackURL
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
            filename: '[name].css'
        }),
        new CopyWebpackPlugin([
            {from: path.resolve(modulesDir, 'mathjax'), to: 'mathjax'}
        ]),
        new webpack.EnvironmentPlugin({
            NODE_ENV: (env ? env.NODE_ENV : null) || 'development'
        })
    ],
    resolve: {
        alias: {
            jquery: 'jquery/src/jquery'
        }
    }
});
