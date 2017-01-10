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

    global.setupLinkingWidget = function setupLinkingWidget(options) {
        options = $.extend(true, {
            fieldId: null
        }, options);

        function updateDropdownState() {
            var $this = $(this);
            if ($this.prop('checked')) {
                $this.closest('.i-radio').siblings('.i-radio').find('.i-linking-dropdown select').prop('disabled', true);
                $this.siblings('.i-linking-dropdown').find('select').prop('disabled', false);
            }
        }

        var field = $('#' + options.fieldId);
        field.find('.i-linking > .i-linking-dropdown > select > option[value=""]').prop('disabled', true);
        field.find('.i-linking.i-radio > input[type="radio"]')
            .off('change').on('change', updateDropdownState)
            .each(updateDropdownState);
    };
})(window);
