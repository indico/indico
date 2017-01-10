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

    global.setupEventCreationDialog = function setupEventCreationDialog(options) {
        options = $.extend({
            categoryField: null,
            protectionModeFields: null,
            initialCategory: null
        }, options);
        var messages = $($.parseHTML($('#event-creation-protection-messages').html()));
        var protectionMessage = $('<div>', {'class': 'form-group', 'css': {'marginTop': '5px'}});
        var currentCategory = null;

        protectionMessage.appendTo(options.protectionModeFields.closest('.form-field'));

        function updateProtectionMessage() {
            var mode = options.protectionModeFields.filter(':checked').val();
            if (mode == 'inheriting') {
                mode = currentCategory.is_protected ? 'inheriting-protected' : 'inheriting-public';
            }
            var elem = messages.filter('.{0}-protection-message'.format(mode));
            elem.find('.js-category-title').text(currentCategory.title);
            protectionMessage.html(elem);
        }

        options.categoryField.on('indico:categorySelected', function(evt, category) {
            if (!currentCategory) {
                options.protectionModeFields.prop('disabled', false);
                options.protectionModeFields.filter('[value=inheriting]').prop('checked', true);
            }
            currentCategory = category;
            updateProtectionMessage();
        });

        options.protectionModeFields.on('change', function() {
            updateProtectionMessage();
        });

        if (options.initialCategory) {
            options.categoryField.trigger('indico:categorySelected', [options.initialCategory]);
        } else {
            options.protectionModeFields.prop('disabled', true);
        }
    };
})(window);
