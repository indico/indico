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

IndicoUI.Widgets = {
    /**
        @namespace Generic, resusable, components
        */
    Generic: {

        /**
         * (DEPRECATED)
         * Creates a tooltip above the given element.
         * Example of usage:
         *
         * var homeButtonPopup = function(event) {
         *     IndicoUI.Widgets.Generic.tooltip(this, event, "<span style='padding:3px'>Go to Indico Home Page</span>");
         * }
         * $E('homeButton').dom.onmouseover = homeButtonPopup;
         *
         * @param {Object} in_this (view example)
         * @param {Object} event (view example)
         * @param {String} content Whatever content is desired.
         */
        tooltip: function(in_this, event, content) {
            var $this = $(in_this);
            if($this.data('hasTooltip')) {
                return;
            }
            $this.data('hasTooltip', true).qtip({
                content: {
                    text: content
                },
                show: {
                    ready: true
                }
            });

            // Return the onmouseout handler in case
            // it needs to be called from outside
            return function() {
                $this.qtip('hide');
            };
        }
    }
};


