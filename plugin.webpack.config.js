// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/no-commonjs, import/unambiguous, import/newline-after-import */
/* global module:false */

const path = require('path');
const process = require('process');
const glob = require('glob');
const merge = require('webpack-merge');
const _ = require('lodash');

const config = require(path.join(process.env.INDICO_PLUGIN_ROOT, 'webpack-build-config'));
const bundles = require(path.join(process.env.INDICO_PLUGIN_ROOT, 'webpack-bundles'));
const base = require(path.join(config.build.indicoSourcePath, 'webpack'));


const entry = bundles.entry || {};
const allThemeFiles = [];

if (!_.isEmpty(config.themes)) {
    const themeFiles = base.getThemeEntryPoints(config, './themes/');
    Object.assign(entry, themeFiles);
    allThemeFiles.push(...Object.values(themeFiles).reduce((acc, current) => acc.concat(current)));
}


function generateModuleAliases() {
    return glob.sync(path.join(config.indico.build.rootPath, 'modules/**/module.json')).map(file => {
        const mod = {produceBundle: true, partials: {}, ...require(file)};
        const dirName = path.join(path.dirname(file), 'client/js');
        const modulePath = path.join('indico/modules', mod.parent || '', mod.name);
        return {
            name: modulePath,
            alias: dirName,
            onlyModule: false
        };
    });
}

module.exports = (env) => {
    return merge.strategy({
        'resolve.alias': 'prepend'
    })(base.webpackDefaults(env, config, bundles), {
        entry,
        externals: {
            jquery: 'jQuery'
        },
        module: {
            rules: [
                {
                    test: /.*\.(jpe?g|png|gif|svg|woff2?|ttf|eot)$/,
                    use: {
                        loader: 'file-loader'
                    }
                }
            ]
        },
        resolve: {
            alias: generateModuleAliases()
        },
        output: {
            jsonpFunction: 'pluginJsonp'
        },
        optimization: {
            splitChunks: {
                cacheGroups: {
                    common: module => {
                        return ({
                            name: 'common',
                            chunks: 'initial',
                            // exclude themes, like we do in the core webpack config
                            minChunks: allThemeFiles.includes(module.resource) ? 9999 : 2
                        });
                    }
                }
            }
        }
    });
};
