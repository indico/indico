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

/*
* This widget extends an *existing* UI button to allow it to be disabled
* and show a a tooltip while it is disabled.
*/
(function($, undefined) {
    $.widget('indico.disabledButtonWithTooltip',  $.extend({}, $.indico.disabledElementWithTooltip, {
        // Default options
        options: {
            elementClass: 'ui-dttbutton'
        },

        _create: function() {
            this.isUIButton = this.element.is('.ui-button');
            if(this.options.disabled === null) {
                this.options.disabled = this.isUIButton ? this.element.button('option', 'disabled') : false;
            }
            $.indico.disabledElementWithTooltip.prototype._create.apply(this, arguments);
        },

        _update: function() {
            if(this.isUIButton) {
                this.element.button(!this.options.disabled ? 'enable' : 'disable');
            }
            else {
                this.element.prop('disabled', this.options.disabled);
            }
            this.overlay.toggle(this.options.disabled);
        },

        destroy: function() {
            $.indico.disabledElementWithTooltip.prototype.destroy.apply(this, arguments);
            // restore ui-state-disabled since super's destroy removed it
            if(this.isUIButton) {
                this.element.button('option', 'disabled', this.options.disabled);
            }
        },

        _setOption: function(key, value) {
            if(key == 'disabled') {
                this.options.disabled = value;
                if(this.isUIButton) {
                    // HACK HACK HACK: We only want the UI disabled class if it's an UI button.
                    // Unfortunately there is no option to control this so we only call the super method
                    // if we have an UI button.
                    $.Widget.prototype._setOption.apply(this, arguments);
                }
                this._update();
            }
            else {
                $.Widget.prototype._setOption.apply(this, arguments);
            }
        }
    }));
})(jQuery);
