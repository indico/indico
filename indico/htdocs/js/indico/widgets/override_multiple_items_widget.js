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

    global.setupOverrideMultipleItemsWidget = function setupOverrideMultipleItemsWidget(options) {
        options = $.extend(true, {
            fieldId: null
        }, options);

        var widget = $('#' + options.fieldId + '-widget');
        var field = $('#' + options.fieldId);
        var data = JSON.parse(field.val());

        widget.on('input change', 'input', function() {
            var $this = $(this);
            if (data[$this.data('key')] === undefined) {
                data[$this.data('key')] = {};
            }
            data[$this.data('key')][$this.data('field')] = $this.val();
            updateField();
        });

        widget.find('input').each(function() {
            var $this = $(this);
            var rowData = data[$this.data('key')] || {};
            $this.val(rowData[$this.data('field')] || '');
        });

        function updateField() {
            field.val(JSON.stringify(data));
        }
    };
})(window);
