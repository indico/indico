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

(function(global) {
    'use strict';

    global.setupSelectizeWidget = function setupSelectizeWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            minTriggerLength: 0,
            searchUrl: null,
            searchMethod: 'GET',
            searchPayload: null,
            selectizeOptions: null,
            selectedItem: null,
            allowById: false,
            preload: false
        }, options);

        function getSearchData(query) {
            var m;
            if (options.allowById && (m = query.match(/^#(\d+)$/))) {
                return {id: m[1]};
            } else if (query.length >= options.minTriggerLength) {
                return {q: query};
            } else if (!query && options.preload) {
                return {};
            } else {
                return null;
            }
        }

        var $field;
        var params = {
            load: function(query, callback) {
                var self = this;
                var data = getSearchData(query);
                if (!data) {
                    return callback();
                }
                if (options.searchPayload) {
                    $.extend(data, options.searchPayload);
                }
                $.ajax({
                    url: options.searchUrl,
                    method: options.searchMethod,
                    data: data,
                    cache: false
                }).fail(function(data) {
                    callback();
                    handleAjaxError(data);
                }).done(function(res) {
                    if (!query && options.preload) {
                        // prevent extra queries after preloading
                        self.settings.load = null;
                    }
                    callback(res);
                    if (options.selectedItem !== null) {
                        $field[0].selectize.setValue(options.selectedItem.id);
                    }
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
                    // disable scoring to avoid reordering
                    var scoreFunc = this.getScoreFunction(query);
                    return function(item) {
                        return scoreFunc(item) ? 1 : 0;
                    };
                }
            }
        };

        _.extend(params, options.selectizeOptions);
        $field = $('#' + options.fieldId);
        $field.selectize(params);

        // disallow removing options
        $field[0].selectize.removeOption = function() {
            return false;
        };
    };
})(window);
