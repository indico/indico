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

(function($) {
    $.widget("indico.scrollblocker", {

        options: {
            overflowType: "scroll"
        },

        _create: function() {
            var element = this.element;
            var options = this.options;

            $("body").on("mousewheel wheel", function (e) {
                var blocker = $(e.target).parentsUntil(element.parent()).filter(function(){
                    return $(this).hasCSS("overflow-y", options.overflowType);
                });

                if (blocker.length > 0) {
                    var wheelup = (e.originalEvent.wheelDelta || -e.originalEvent.deltaY) / 120 > 0;

                    if (blocker.scrollTop() === 0 && wheelup) {
                        return false;
                    }

                    if ((blocker.scrollTop()+1 >= (blocker.prop("scrollHeight") - blocker.outerHeight())) && !wheelup) {
                        return false;
                    }
                }

                return true;
            });
        }
    });
})(jQuery);
