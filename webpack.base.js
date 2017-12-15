const chalk = require('chalk');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const uglify = require('uglify-js');

const webpack = require('webpack')

const CopyWebpackPlugin = require('copy-webpack-plugin');
const ExtractTextPlugin = require('extract-text-webpack-plugin')
const ManifestPlugin = require('webpack-manifest-plugin');
const ProgressBarPlugin = require('progress-bar-webpack-plugin');

function hashFile(filePath) {
    // Return the md5 hash of the file's contents
    const h = crypto.createHash('md5');
    h.update(fs.readFileSync(filePath));
    return h.digest('hex').slice(0, 8);
}

const resolveAlias = [
    {name: 'jquery', alias: 'jquery/src/jquery', onlyModule: false}
];

function webpackDefaults(env, config, clientDir, entryPoints) {
    const currentEnv = (env ? env.NODE_ENV : null) || 'development';
    const modulesDir = path.join(config.build.rootPath, '..', 'node_modules');

    function fileLoaderPublicPathGenerator(_prefix, nodeModules) {
        return (filePath) => {
            let pathParts = filePath.split(path.sep);
            let prefix = _prefix;

            // if no prefix specified, take the first parh segment
            if (!prefix) {
                prefix = pathParts[0];
                pathParts = pathParts.slice(1);
            }

            let sourcePath = null;
            if (nodeModules) {
                // this is kind of ugly, but we can't access the actual source file at this point
                sourcePath = path.resolve(modulesDir, filePath.replace(/mod_assets\/(?:_\/)+node_modules\//, ''));
            } else {
                sourcePath = path.resolve(config.build.staticPath, _prefix || '', filePath);
            }

            const hash = hashFile(sourcePath);
            const newPath = path.join(prefix, 'v', hash, ...pathParts);
            return config.build.staticURL + newPath;
        };
    }

    // Minification of copied files (e.g. CKEditor and MathJax)
    const transform = currentEnv === 'development' ? null : (content, path) => {
        if (!path.match(/\.js$/)) {
            return content;
        }
        return uglify.minify(content.toString(), {fromString: true}).code;
    };

    const _cssLoaderOptions = {
        root: config.build.staticPath,
        sourceMap: true
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
                            emitFile: false,
                            publicPath: fileLoaderPublicPathGenerator()
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
                            outputPath: 'mod_assets/',
                            publicPath: fileLoaderPublicPathGenerator('dist', true)
                        }
                    }
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
                    // Let's not extract theme SCSS into the common chunk
                    // Otherwise we will have no theme SCSS files.
                    if (mod.resource.match(/styles\/themes\//)) {
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
            new CopyWebpackPlugin([
                {from: path.resolve(modulesDir, 'ckeditor/dev/builder/release/ckeditor'), to: 'js/ckeditor', transform},
                {from: path.resolve(modulesDir, 'mathjax'), to: 'js/mathjax', transform}
            ]),
            new ProgressBarPlugin({
                format: chalk.cyan('Code being sent to the moon and back \u{1f680} \u{1f311}') + '  [:bar] ' +
                    chalk.green.bold(':percent') + ' (:elapsed seconds)'
            })
        ],
        resolve: {
            alias: resolveAlias
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

module.exports = {resolveAlias, webpackDefaults};
