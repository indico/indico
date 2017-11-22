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

(function($) {
    $.widget("indico.indicoColorpicker", {
        updateWidget: function() {
            this.$preview.toggleClass('no-value', !this.$colorInput.val().length);
            const val = this.$colorInput.val();
            if (!val) {
                this.$preview.attr('style', null);
            }
        },

        _create: function() {
            let oldValue;
            const $element = this.element;
            const $preview = this.$preview = $element.find('.color-preview');
            const $colorInput = this.$colorInput = $element.find('input');

            $colorInput.colorpicker({
                colorFormat: '#HEX',
                altField: $preview,
                open: () => {
                    oldValue = $colorInput.val();
                },
                ok: () => {
                    this.updateWidget();
                },
                select: () => {
                    this.updateWidget();
                },
                cancel: () => {
                    $colorInput.val(oldValue);
                    this.updateWidget();
                    $colorInput.trigger('cancel');
                }
            });

            this.updateWidget();
        }
    });
})(jQuery);
