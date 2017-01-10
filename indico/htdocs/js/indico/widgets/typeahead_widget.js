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

    global.setupTypeaheadWidget = function setupTypeaheadWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            minTriggerLength: 0,
            data: null,
            typeaheadOptions: null,
            searchUrl: null
        }, options);

        var field = $('#' + options.fieldId);
        var params = {
            hint: true,
            cancelButton: false,
            mustSelectItem: true,
            minLength: options.minTriggerLength,
            source: {
                data: options.data
            }
        };

        if (options.searchUrl) {
            $.extend(true, params, {
                dynamic: true,
                source: {
                    url: [{
                        url: options.searchUrl,
                        data: {
                            q: '{{query}}'
                        }
                    }]
                }
            });
        }

        field.typeahead($.extend(true, params, options.typeaheadOptions));
    };
})(window);
