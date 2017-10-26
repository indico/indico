var ManifestPlugin = require('webpack-manifest-plugin');
var config = require('./config');
var webpack = require('webpack')


module.exports = {
    devtool: 'source-map',
    context: __dirname + "/indico/web/client",
    entry: "./js/index.js",
    output: {
        path: config.build.assetsPath,
        filename: "bundle.js",
        publicPath: config.build.assetsURL
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                loader: 'babel-loader',
                exclude: /node_modules/
            },
            {
                include: /jquery-migrate/,
                parser: {
                    amd: false
                }
            }
        ]
    },
    plugins: [
        new ManifestPlugin({
            fileName: 'manifest.json',
            stripSrc: true,
            publicPath: config.build.assetsURL
        }),
        new webpack.ProvidePlugin({
            $: 'jquery',
            _: 'underscore'
        })
    ],
    resolve: {
        alias: {
            jquery: 'jquery/src/jquery'
        }
    }
};
