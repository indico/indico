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
import importOnce from 'node-sass-import-once';


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
    const indicoClientPath = path.join(config.isPlugin ? config.indico.build.clientPath : config.build.clientPath,
                                       'styles');
    const rootPath = path.join(config.build.rootPath);

    return Object.assign(...Object.keys(themes).map((k) => {
        const returnValue = {};
        const escapedKey = k.replace('-', '_');

        returnValue['themes_' + escapedKey] =
            [_resolveTheme(rootPath, indicoClientPath, prefix + themes[k].stylesheet)];

        if (themes[k].print_stylesheet) {
            returnValue['themes_' + escapedKey + '.print'] =
                [_resolveTheme(rootPath, indicoClientPath, prefix + themes[k].print_stylesheet)];
        }
        return returnValue;
    }));
}

export function generateAssetPath(config, virtualVersion = false) {
    // /css/whatever.css => /css/whatever__v123abcdef.css
    return (file) => {
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

export function webpackDefaults(env, config) {
    const currentEnv = (env ? env.NODE_ENV : null) || 'development';
    const nodeModules = [path.join(config.build.indicoSourcePath || path.resolve(config.build.rootPath, '..'),
                                   'node_modules')];

    if (config.isPlugin) {
        // add plugin's node_modules in addition to the core's
        nodeModules.push(path.resolve(config.build.rootPath, '../node_modules'));
    }

    const _cssLoaderOptions = {
        root: config.indico ? config.indico.build.staticPath : config.build.staticPath,
        url: true
    };

    const scssIncludePath = path.join((config.isPlugin ?
        path.resolve(config.build.indicoSourcePath, './indico/web/client') :
        path.join(config.build.clientPath)),
                                      'styles');

    function getDevtoolFilename(info) {
        const root = path.resolve(config.indico ? config.indico.build.rootPath : config.build.rootPath, '..');
        return path.relative(root, info.absoluteResourcePath);
    }
    const indicoClientPath = config.isPlugin ? config.indico.build.clientPath : config.build.clientPath;

    return {
        devtool: 'source-map',
        context: config.build.clientPath,
        output: {
            path: config.build.distPath,
            filename: "js/[name].[chunkhash:8].bundle.js",
            publicPath: config.build.distURL,
            devtoolModuleFilenameTemplate: (info) => `webpack:///${getDevtoolFilename(info)}`,
            devtoolFallbackModuleFilenameTemplate: (info) => `webpack:///${getDevtoolFilename(info)}?${info.hash}`,
        },
        module: {
            rules: [
                {
                    test: /\.js$/,
                    loader: 'babel-loader',
                    exclude: /node_modules/,
                    options: {
                        extends: path.resolve(config.indico ? config.indico.build.rootPath : config.build.rootPath,
                                              '..', '.babelrc'),
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
                            options: {
                                root: config.indico ? config.indico.build.staticPath : config.build.staticPath,
                                sourceMap: true,
                                url: !config.isPlugin, // FIXME: true breaks plugins, false breaks /indico/ in core
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
                                sourceMap: true,
                                includePaths: [scssIncludePath],
                                outputStyle: 'compact',
                                importer: importOnce,
                            }
                        }],
                    })
                }
            ]
        },
        plugins: [
            new ManifestPlugin({
                fileName: 'manifest.json',
                publicPath: config.build.distURL
            }),
            // Do not load moment locales (we'll load them explicitly)
            new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),
            new ExtractTextPlugin({
                filename: 'css/[name].[md5:contenthash:hex:8].css'
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
                {name: 'indico', alias: path.join(indicoClientPath, 'js/')}
            ]
        },
        resolveLoader: {
            modules: nodeModules
        },
        externals: (context, request, callback) => {
            // tell webpack to make selectize use window.jQuery (and not load it again)
            if (/^jquery$/.test(request) && /selectize/.test(context)) {
                return callback(null, 'jQuery')
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
            chunksSort: 'name'
        },
        mode: currentEnv,
        optimization: {
            splitChunks: {
                cacheGroups: {
                    // 'common' chunk, which should include common dependencies
                    common: (module) => {
                        return {
                            name: "common",
                            chunks: "initial",
                            // theme CSS files shouldn't be included in the
                            // common.css chunk, otherwise they will interfere
                            // with interface CSS
                            minChunks: /styles\/themes/.test(module.request) ? 9999 : 2
                        }
                    }
                }
            }
        }
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
            }
        }
    };
}
