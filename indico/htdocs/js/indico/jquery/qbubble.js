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

(function($) {
    $.widget('indico.qbubble', {
        defaultQtipOptions: {
            overwrite: true,
            position: {
                my: 'top center',
                at: 'bottom center',
                adjust: {
                    mouse: false,
                    scroll: false
                }
            },
            show: {
                event: 'click',
                solo: true
            },
            hide: {
                event: 'unfocus click'
            }
        },

        _create: function() {
            var self = this;
            var classes = self.options.style ? self.options.style.classes : '';

            self.element.qtip($.extend(true, {}, self.defaultQtipOptions, self.options, {
                style: {classes: 'qbubble ' + classes}
            }));

            this._on({
                click: function(evt) {
                    evt.preventDefault();
                }
            });
        },

        api: function() {
            var self = this;
            return self.element.qtip('api');
        },

        destroy: function() {
            var self = this;
            self.element.qtip('destroy');
        },

        hide: function() {
            var self = this;
            self.element.qtip('hide');
        },

        option: function(entry, value) {
            var self = this;
            self.element.qtip('option', entry, value);
        }
    });
})(jQuery);
