/*
* -*- mode: text; coding: utf-8; -*-


   This file is part of Indico.
   Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).

   Indico is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation; either version 3 of the
   License, or (at your option) any later version.

   Indico is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with Indico; if not, see <http://www.gnu.org/licenses/>.
*/

(function($) {
    $.widget("indico.clearableinput", {
        options: {
            callback: function() {},
            clearClass: "clearableinput",
            emptyvalue: "",
            focusAfter: true
        },

        _create: function() {
            var self = this;
            var opt = self.options;
            var input = self.element;

            var clear = $('<span class="icon-close"></span>')
                .css("line-height", input.css("height"))
                .click(function() {
                    self._clear();
                });

            input.wrap($('<span class="' + opt.clearClass + '"></span>'))
                .after(clear)
                .on("input propertychange", function() {
                    if (input.val() === "") {
                        clear.css("visibility", "hidden");
                    } else {
                        clear.css("visibility", "visible");
                    }
                })
                .on("keyup", function(e) {
                    if (e.which == K.ESCAPE) {
                        input.val('value');
                        self._clear();
                    }
                });
        },

        _clear: function() {
            var self = this;
            var opt = self.options;
            var input = self.element;

            input.val(opt.emptyvalue).trigger("propertychange");
            if (opt.focusAfter) {
                input.focus();
            } else {
                input.blur();
            }
            opt.callback();
        }
    });
})(jQuery);
