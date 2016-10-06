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
            selectizeOptions: null,
            allowById: false
        }, options);

        function getSearchData(query) {
            var m;
            if (options.allowById && (m = query.match(/^#(\d+)$/))) {
                return {id: m[1]};
            } else if (query.length >= options.minTriggerLength) {
                return {q: query};
            } else {
                return null;
            }
        }

        var params = {
            load: function(query, callback) {
                var data = getSearchData(query);
                if (!data) {
                    return callback();
                }
                $.ajax(options.searchUrl, {
                    data: data,
                    cache: false
                }).fail(function() {
                    callback();
                }).done(function(res) {
                    callback(res);
                });
            },
            score: function(query) {
                var data = getSearchData(query);
                if (data && data.id !== undefined) {
                    // when searching by ID ensure we don't get other results from selectize's internal cache
                    return function(item) {
                        return +(item.friendly_id === +data.id);
                    };
                } else {
                    var scoreFunc = this.getScoreFunction(query);
                    return function(item) {
                        return scoreFunc(item);
                    };
                }
            }
        };

        _.extend(params, options.selectizeOptions);
        var $field = $('#' + options.fieldId);
        $field.selectize(params);

        // disallow removing options
        $field[0].selectize.removeOption = function() {
            return false;
        };
    };
})(window);
