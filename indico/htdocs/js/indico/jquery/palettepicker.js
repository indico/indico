/* This file is part of Indico.
 * Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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
    $.widget('indico.palettepicker', {

        options: {
            availableColors: [],
            onSelect: null,
            numColumns: 5
        },

        _create: function() {
            var self = this;
            var element = this.element;
            var palette = $('<div>', {'class': 'color-palette', 'css': {'display': 'none'}});
            var paletteTable = $('<table>');
            var trigger = this.element.find('.switch-trigger');
            var availableColors = this.options.availableColors;
            var tr = this._createTableRow();

            for (var i = 0; i < availableColors.length; ++i) {
                var td = $('<td>', {
                    'css': {'background': '#' + availableColors[i].background},
                    'class': 'palette-color'
                });

                var colorBox = $('<div>', {
                    'value': '#' + availableColors[i].background,
                    'class': 'background-box'
                });

                colorBox.append($('<div>', {
                    'css': {'background': '#' + availableColors[i].text},
                    'class': 'text-box',
                    'value': '#' + availableColors[i].text
                }));

                td.on('click', function(evt) {
                    evt.preventDefault();

                    var $this = $(this),
                        backgroundColor = $this.find('.background-box').val(),
                        textColor = $this.find('.text-box').val();

                    trigger.css({'background': backgroundColor, 'color': textColor + ' !important'});

                    if (self.options.onSelect) {
                        self.options.onSelect.call(trigger, backgroundColor, textColor);
                    }

                    palette.hide();
                });

                td.append(colorBox);
                tr.append(td);

                if ((i + 1) % this.options.numColumns == 0) {
                    paletteTable.append(tr);
                    tr = this._createTableRow();
                }
            }

            if (tr.children().length) {
                paletteTable.append(tr);
            }

            palette.append(paletteTable);
            palette.appendTo(this.element);

            trigger.on('click', function() {
                palette.toggle();
            });

            $(document).on('click', function(evt) {
                var $target = $(evt.target);
                if ($target.hasClass('switch-trigger')) {
                    if ($target.hasClass('active-color-switch')) {
                        $('.switch-trigger:not(.active-color-switch) .color-palette').hide();
                    } else {
                        var activePalettePicker = $('.switch-trigger.active-color-switch');
                        if (activePalettePicker.length) {
                            activePalettePicker.removeClass('active-color-switch').next('.color-palette').hide();
                        }
                        $target.addClass('active-color-switch');
                    }
                } else {
                    $('.switch-trigger').removeClass('active-color-switch');
                    $('.color-palette').hide();
                }
            });
        },
        _createTableRow: function() {
            return $('<tr>', {'height': 13});
        }
    });
})(jQuery);
