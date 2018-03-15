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

(function(global) {

    global.setupColorPickerWidget = function setupColorPickerWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            showField: true
        }, options);

        var $formField = $('#' + options.fieldId);
        var $colorField = $formField.closest('.i-color-field');

        $colorField.indicoColorpicker();
        if (options.showField) {
            $formField.clearableinput({
                focusOnClear: false,
                onClear: () => {
                    $colorField.indicoColorpicker('updateWidget');
                }
            });
        } else {
            $formField.hide();
        }

        // Hack to set clearable input whenever the color changes
        $formField.on('change', () => {
            $formField.clearableinput('setValue', $formField.val());
        }).on('cancel', () => {
            $formField.clearableinput('setValue', $formField.val());
        });
    };
})(window);
