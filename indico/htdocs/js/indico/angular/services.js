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

var ndServices = angular.module('ndServices', []);

ndServices.provider('url', function() {
    var baseUrl = Indico.Urls.Base;
    var modulePath = '';
    // XXX: don't remove the () around `+Date.now()`
    // the minifier converts this to `'?'++Date.now()` which is a syntax error
    var debug = $('body').data('debug') ? '?' + (+Date.now()) : '';

    return {
        setModulePath: function(path) {
            if (path.substr(-1) == '/') {
                path = path.substr(0, path.length - 1);
            }

            modulePath = path;
        },

        $get: function() {
            return {
                tpl: function(path) {
                    return baseUrl + modulePath + '/tpls/' + path + debug;
                }
            };
        }
    };
});
