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

import {createHash} from 'crypto';
import chalk from 'chalk';
import fs from 'fs';
import path from 'path';

import webpack from 'webpack';

import ExtractTextPlugin from 'extract-text-webpack-plugin';
import ManifestPlugin from 'webpack-manifest-plugin';
import ProgressBarPlugin from 'progress-bar-webpack-plugin';


function _resolveTheme(rootPath, indicoClientPath, filePath) {
    const indicoRelativePath = path.resolve(indicoClientPath, filePath);

    if (indicoClientPath && !fs.existsSync(path.resolve(rootPath, filePath)) &&
            fs.existsSync(indicoRelativePath)) {
        return path.resolve(indicoClientPath, filePath);
    }

    return path.resolve(rootPath, filePath);
}

export function getThemeEntryPoints(config, prefix) {
    const themes = config.themes;
    const indicoClientPath = path.join(config.isPlugin ? config.indico.build.clientPath :
                                       config.build.clientPath, 'styles');
    const rootPath = path.join(config.build.rootPath);

    return Object.assign(...Object.keys(themes).map((k) => {
        const returnValue = {};
        const escapedKey = k.replace('-', '_');

        returnValue['themes_' + escapedKey] =
            _resolveTheme(rootPath, indicoClientPath, prefix + themes[k].stylesheet);

        if (themes[k].print_stylesheet) {
            returnValue['themes_' + escapedKey + '.print'] =
                _resolveTheme(rootPath, indicoClientPath, prefix + themes[k].print_stylesheet);
        }
        return returnValue;
    }));
}

export function generateAssetPath(config) {
    // /css/whatever.css => /css/v/123abcde/whatever.css
    return (file) => {
        const relPath = path.relative(config.build.staticPath, file);
        const {dir, base} = path.parse(relPath);
        const h = createHash('md5');
        h.update(fs.readFileSync(file));
        // .. -> _, like file-loader does
        return path.join(dir.replace(/\.\./g, '_'), 'v', h.digest('hex').slice(0, 8), base);
    };
}

export function webpackDefaults(env, config) {
    const currentEnv = (env ? env.NODE_ENV : null) || 'development';

    const _cssLoaderOptions = {
        root: config.indico ? config.indico.build.staticPath : config.build.staticPath,
        url: true
    };

    return {
        devtool: 'source-map',
        context: config.build.clientPath,
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
                            options: {
                                root: config.indico ? config.indico.build.staticPath : config.build.staticPath,
                                sourceMap: true,
                                url: false
                            }
                        }, {
                            loader: 'postcss-loader',
                            options: {
                                sourceMap: true,
                                config: {
                                    path: path.join(config.indico ? config.indico.build.rootPath :
                                                                    config.build.rootPath,
                                                    'postcss.config.js'),
                                    ctx: {
                                        urlnamespaces: {
                                            namespacePaths: (name) => {
                                                return path.join(config.indico.build.staticURL, 'static/plugins', name);
                                            }
                                        }
                                    }
                                }
                            }
                        }, {
                            loader: 'sass-loader',
                            options: {
                                sourceMap: currentEnv === 'development',
                                includePaths: [path.join(config.build.clientPath, 'styles')]
                            }
                        }],
                    })
                }
            ]
        },
        plugins: [
            new ManifestPlugin({
                fileName: 'manifest.json',
                publicPath: config.build.distURL,
                map: (file) => {
                    // change only files that are part of chunks
                    if (file.chunk) {
                        const hash = file.chunk.renderedHash.slice(0, 8);
                        file.path = file.path.replace(/\/dist\//, `/dist/v/${hash}/`);
                    }
                    return file;
                }
            }),
            new webpack.ProvidePlugin({
                $: 'jquery',
                jQuery: 'jquery',
                _: 'underscore',
                moment: 'moment'
            }),
            new webpack.optimize.CommonsChunkPlugin({
                name: 'common',
                minChunks: (mod, count) => {
                    if (config.isPlugin) {
                        // Plugin files should be loaded in their entirety
                        return false;
                    } else if (mod.resource.match(/\/themes\/.*\.scss/)) {
                        // Let's not extract theme SCSS into the common chunk
                        // Otherwise we will have no theme SCSS files.
                        // This check is quite hacky as it relies of the file path,
                        // we should find some better way to control this threshold.
                        return false;
                    } else {
                        return count >= 3;
                    }
                }
            }),
            // Do not load moment locales (we'll load them explicitly)
            new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),
            new ExtractTextPlugin({
                filename: 'css/[name].css'
            }),
            new webpack.EnvironmentPlugin({
                NODE_ENV: currentEnv
            }),
            new ProgressBarPlugin({
                format: chalk.cyan('Code being sent to the moon and back \u{1f680} \u{1f311}') + '  [:bar] ' +
                    chalk.green.bold(':percent') + ' (:elapsed seconds)'
            })
        ],
        resolve: {
            alias: [
                {name: 'jquery', alias: 'jquery/src/jquery', onlyModule: false}
            ]
        },
        stats: {
            assets: false,
            children: false,
            modules: false,
            chunks: true,
            chunkModules: false,
            chunkOrigins: false,
            chunksSort: 'name'
        }
    };
}

export function indicoStaticLoader(config) {
    return {
        test: /\/static\/(images|fonts)\/.*\.(jpe?g|png|gif|svg|woff2?|ttf|svg|eot)$/,
        use: {
            loader: 'file-loader',
            options: {
                name: generateAssetPath(config),
                context: config.build.staticPath,
                emitFile: false,
                publicPath: '/'
            }
        }
    };
}
