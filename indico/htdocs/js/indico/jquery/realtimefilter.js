/* This file is part of Indico.
 * Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
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
    $.widget("indico.realtimefilter", {

        options: {
            callback: function() {},
            wait: 250
        },

        _create: function() {
            var self = this;
            var element = self.element;
            var callback = self.options.callback;
            var wait = self.options.wait;

            function delayedCallback() {
                setTimeout(function() {
                    callback();
                }, wait);
            }

            element.clearableinput({
                callback: function() {
                    delayedCallback();
                }
            });

            element.typeWatch({
                callback: function() {
                    callback();
                },
                wait: wait,
                highlight: true,
                captureLength: 0
            });

            element.on("cut paste", function() {
                delayedCallback();
            });
        }
    });
})(jQuery);
