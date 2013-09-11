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
            validation: function(e) { return true; },
            clearable: true,
            emptyvalue: "",
            invalidclass: "invalid",
            wait: 250
        },

        _create: function() {
            var self = this;
            var element = self.element;
            var opt = self.options;

            element.typeWatch({
                callback: function() {
                    self._callback();
                },
                wait: opt.wait,
                highlight: false,
                captureLength: 0
            });

            if (opt.clearable) {
                element.clearableinput({
                    callback: function() {
                        self._delayedCallback();
                    },
                    emptyvalue: opt.emptyvalue
                });
            }

            element.on("cut paste", function() {
                self._delayedCallback();
            });

            element.on("focusout", function() {
                if ($(this).val() === "") {
                    $(this).val(opt.emptyvalue);
                }
            });
        },

        update: function(delayed) {
            var self = this;

            if (delayed) {
                self._delayedCallback();
            } else {
                self._callback();
            }
        },

        validate: function() {
            var self = this;
            return self.options.validation(self.element);
        },

        _callback: function() {
            var self = this;
            var element = self.element;
            var opt = self.options;

            if (opt.validation(element)) {
                element.removeClass(opt.invalidclass);
                opt.callback();
            } else {
                element.addClass(opt.invalidclass);
            }
        },

        _delayedCallback: function() {
            var self = this;

            setTimeout(function() {
                self._callback();
            }, self.options.wait);
        }
    });
})(jQuery);
