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
    $.widget("indico.colorpicker", {

        options: {
            defaultColor: "ffffff"
        },

        _create: function() {
            var self = this;
            var element = self.element;
            var opt = self.options;
            var clickableWrapper = element.find('.clickable-wrapper');
            var preview = element.find('.color-preview');
            var colorInput = element.find('input');

            var updateColorPreview = function(color){
                preview.css('background', color);
            };

            colorInput.on('keyup', function() {
                preview.toggleClass('no-value', !colorInput.val().length)
                if (colorInput.val()) {
                    updateColorPreview(colorInput.val());
                    clickableWrapper.ColorPickerSetColor(colorInput.val());
                }
                else {
                    preview.attr('style', null);
                }
            });

            colorInput.trigger('keyup');

            clickableWrapper.ColorPicker({
                color: opt.defaultColor,
                onSubmit: function(hsb, hex, rgb, el) {
                        $(el).val(hex);
                        updateColorPreview('#' + hex);
                        $(el).ColorPickerHide();
                },
                onChange: function (hsb, hex, rgb) {
                        colorInput.val('#' + hex);
                        updateColorPreview('#' + hex);
                        colorInput.trigger('input');
                },
                onShow: function (colorpicker) {
                    $(colorpicker).fadeIn(500);
                    return false;
                },
                onHide: function (colorpicker) {
                    $(colorpicker).fadeOut(500);
                    return false;
                }
            });
        }
    });
})(jQuery);
