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
    $.widget('indico.palettepicker', {

        options: {
            availableColors: [],
            onSelect: null,
            numColumns: 5
        },

        _create: function() {
            var self = this;
            var element = this.element;
            var paletteTable = $('<table>', {'class': 'palette-picker'});
            var availableColors = this.options.availableColors;
            var tr = this._createTableRow();

            $.each(availableColors, function(index, color) {
                var td = $('<td>', {
                    'css': {'background': '#' + color.background},
                    'class': 'palette-color',
                    'data': {color: color}
                });

                var colorBox = $('<div>', {
                    'class': 'background-box'
                });

                colorBox.append($('<div>', {
                    'css': {'background': '#' + color.text},
                    'class': 'text-box'
                }));

                td.append(colorBox);
                tr.append(td);

                if ((index + 1) % self.options.numColumns == 0) {
                    paletteTable.append(tr);
                    tr = self._createTableRow();
                }
            });

            if (tr.children().length) {
                paletteTable.append(tr);
            }

            paletteTable.on('click', '.palette-color', function() {
                var $this = $(this),
                    color = $this.data('color'),
                    backgroundColor = '#' + color.background,
                    textColor = '#' + color.text,
                    styleObject = element[0].style;

                styleObject.setProperty('color', textColor, 'important');
                styleObject.setProperty('background', backgroundColor, 'important');

                if (self.options.onSelect) {
                    self.options.onSelect.call(element, backgroundColor, textColor);
                }

                element.qtip('hide');
            });

            element.qtip({
                prerender: false,
                overwrite: false,
                style: {
                    classes: 'palette-picker-qtip'
                },
                position: {
                    my: 'top center',
                    at: 'bottom center',
                    target: element,
                    adjust: {
                        mouse: false,
                        scroll: false
                    }
                },
                content: {
                    text: paletteTable
                },
                show: {
                    event: 'click',
                    solo: true
                },
                hide: {
                    event: 'unfocus'
                }
            });
        },
        _createTableRow: function() {
            return $('<tr>', {'height': 13});
        }
    });
})(jQuery);
