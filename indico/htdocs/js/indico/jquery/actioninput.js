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
    'use strict';

    $.widget('indico.actioninput', $.indico.clearableinput, {
        options: {
            actionCallback: function() {},
            actionIcon: 'icon-checkmark',
            alwaysClearable: true,
            enterKeyEnabled: true
        },

        _create: function() {
            var self = this;
            var input = self.element;

            self._super();

            self.actionIcon = $('<a class="i-link accept hide-if-locked {0}"></a>'.format(self.options.actionIcon))
                .css("line-height", input.css("height"))
                .click(function() {
                    self._action();
                });

            input.on("keydown keypress", function(e) {
                if (e.which === K.ENTER && self.options.enterKeyEnabled) {
                    self._action();
                }
            });

            self.buttonBox.prepend(self.actionIcon);
            input.addClass('actionabletext');
        },

        _action: function() {
            var self = this;
            var opt = self.options;
            var input = self.element;

            opt.actionCallback();

            if (opt.focusOnClear) {
                input.focus();
            } else {
                input.blur();
            }
        },

        initSize: function(fontSize, lineHeight) {
            var self = this;

            self._super(fontSize, lineHeight);
            self.actionIcon.css('font-size', self.size.fontSize);
            self.actionIcon.css('line-height', self.size.lineHeight);
        },

        setIconsVisibility: function(visibility) {
            var self = this;

            self._super(visibility);
            self.actionIcon.css('visibility', visibility);
        }
    });
})(jQuery);
