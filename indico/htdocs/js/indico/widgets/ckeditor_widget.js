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

/* global RichTextEditor:false, $E:false */

(function(global) {
    'use strict';

    global.setupCKEditorWidget = function setupCKEditorWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            simple: false,
            images: false,
            height: 475
        }, options);

        var field = $('#' + options.fieldId);
        var editor = new RichTextEditor(600, options.height, options.simple, options.images);
        editor.set(field.val());
        editor.onLoad(function() {
            editor.onChange(function() {
                field.val(editor.get()).trigger('change');
            });
        });
        $E(options.fieldId + '-editor').set(editor.draw());
        // Re-position the dialog if we have one since the initial position is
        // wrong due to the editor being loaded after the dialog has been opened.
        var dialog = field.closest('.ui-dialog-content');
        if (dialog.length) {
            dialog.dialog('option', 'position', dialog.dialog('option', 'position'));
        }
    };
})(window);
