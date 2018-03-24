/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

/* eslint-disable import/no-commonjs, import/unambiguous, import/newline-after-import */
/* global module:false */

const path = require('path');
const process = require('process');
const merge = require('webpack-merge');
const _ = require('lodash');

const config = require(path.join(process.env.INDICO_PLUGIN_ROOT, 'webpack-build-config'));
const bundles = require(path.join(process.env.INDICO_PLUGIN_ROOT, 'webpack-bundles'));
const base = require(path.join(config.build.indicoSourcePath, 'webpack'));


const entry = bundles.entry || {};
if (!_.isEmpty(config.themes)) {
    Object.assign(entry, base.getThemeEntryPoints(config, './themes/'));
}

module.exports = (env) => {
    return merge(base.webpackDefaults(env, config), {
        entry,
        externals: {
            jquery: 'jQuery',
            moment: 'moment'
        }
    });
};
