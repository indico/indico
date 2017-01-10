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

    global.setupPrincipalWidget = function setupPrincipalWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            eventId: null,
            required: false,
            allowExternal: false
        }, options);

        var field = $('#' + options.fieldId);
        var button = $('#choose-' + options.fieldId);
        var display = $('#display-' + options.fieldId);

        if (!options.required) {
            display.clearableinput({
                clearOnEscape: false,
                focusOnClear: false,
                onClear: function() {
                    field.principalfield('remove');
                }
            });
        }

        field.principalfield({
            eventId: options.eventId,
            allowExternalUsers: options.allowExternal,
            enableGroupsTab: false,
            render: function(users) {
                var name = users[0] ? users[0].name : '';
                if (!options.required) {
                    display.clearableinput('setValue', name);
                } else {
                    display.val(name);
                }
            }
        });

        display.add(button).on('click', function() {
            field.principalfield('choose');
        });
    };
})(window);
