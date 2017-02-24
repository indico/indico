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

IndicoUI.Effect = {
    /**
        * Simple CSS manipulation that sets the element's 'display' property to a new style
        * @param {XElement} element the target element
        * @param {string} newStyle the new display style, e.g.: "inline", "block", "table-row".
        *                 If not existant, will be set to '', which usually restores the default style of the element.
        */
    appear: function(element, newStyle){
        if (!exists(newStyle)) {
            newStyle = '';
        }
        element.dom.style.display = newStyle;
    },

    /**
        * Simple CSS manipualtion that sets the element's
        * 'display' property to 'none'
        * @param {XElement} element the target element
        */
    disappear: function(element){
        element.dom.style.display = 'none';
    },

    followScroll: function() {
        $.each($('.follow-scroll'),function(){
            if (!$(this).data('original-offset')) {
                $(this).data('original-offset', $(this).offset());
            }

            var eloffset = $(this).data('original-offset');
            var windowpos = $(window).scrollTop();
            if(windowpos > eloffset.top) {
                if (!$(this).hasClass("scrolling")) {
                    $(this).data({
                        "original-left": $(this).css("left"),
                        "original-width": $(this).css("width")
                    });
                    $(this).css("width", $(this).width());
                    $(this).css("left", eloffset.left);
                    $(this).addClass('scrolling');
                }
            } else {
                if ($(this).hasClass("scrolling")) {
                    $(this).css("left", $(this).data("original-left"));
                    $(this).css("width", $(this).data("original-width"));
                    $(this).removeClass('scrolling');
                }
            }
        });
    }
};

