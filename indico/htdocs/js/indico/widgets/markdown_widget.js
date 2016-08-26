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

    global.setupMarkdownWidget = function setupMarkdownWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            useMarkdownEditor: false
        }, options);

        if (options.useMarkdownEditor) {
            var field = $('#' + options.fieldId);
            var container = field.closest('[data-field-id]');
            field.pagedown();

            ['markdown-info', 'latex-info', 'wmd-help-button'].forEach(function(name) {
                var content = container.find('.{0}-text'.format(name));
                container.find('.' + name).qtip({
                    content: content.html(),
                    hide: {
                        event: 'unfocus'
                    },
                    show: {
                        solo: true
                    },
                    style: {
                        classes: 'informational markdown-help-qtip'
                    }
                }).on('click', function(evt) {
                    evt.preventDefault();
                });
            });
        }
    };
})(window);
