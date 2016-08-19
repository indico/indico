/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

(function(global) {
    'use strict';

    global.setupSelectizeWidget = function setupSelectizeWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            minTriggerLength: 0,
            searchUrl: null,
            selectizeOptions: null
        }, options);

        var params = {
            load: function(query, callback) {
                if (query.length < options.minTriggerLength) {
                    return callback();
                }
                $.ajax(options.searchUrl, {
                    data: {q: query},
                    cache: false
                }).fail(function() {
                    callback();
                }).done(function(res) {
                    callback(res);
                });
            }
        };

        _.extend(params, options.selectizeOptions);
        $('#' + options.fieldId).selectize(params);
    };
})(window);
