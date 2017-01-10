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

    $.widget('indico.palettepicker', {

        options: {
            availableColors: [],
            onSelect: null,
            numColumns: 5,
            selectedColor: null,
            qtipConstructor: null
        },

        _create: function() {
            var self = this;
            var element = this.element;
            var paletteTable = $('<table>', {class: 'palette-picker'});
            var availableColors = this.options.availableColors;
            var tr = this._createTableRow();

            self._paletteTable = paletteTable;

            $.each(availableColors, function(index, color) {
                var td = $('<td>', {
                    class: 'palette-color',
                    data: {color: color}
                });

                var colorBox = $('<div>', {
                    css: {background: '#' + color.background},
                    class: 'background-box'
                });

                colorBox.append($('<div>', {
                    css: {background: '#' + color.text},
                    class: 'text-box'
                }));

                td.append(colorBox);
                tr.append(td);

                if ((index + 1) % self.options.numColumns === 0) {
                    paletteTable.append(tr);
                    tr = self._createTableRow();
                }
            });

            if (tr.children().length) {
                paletteTable.append(tr);
            }

            paletteTable.on('click', '.palette-color', function() {
                var $this = $(this);
                var color = $this.data('color');
                var backgroundColor = '#' + color.background;
                var textColor = '#' + color.text;
                var styleObject = element[0].style;

                self.options.selectedColor = color;
                self._updateSelection();

                styleObject.setProperty('color', textColor, 'important');
                styleObject.setProperty('background', backgroundColor, 'important');

                if (self.options.onSelect) {
                    self.options.onSelect.call(element, backgroundColor, textColor);
                }

                element.qtip('hide');
            });

            var qtipOptions = {
                prerender: false,
                overwrite: false,
                suppress: false,
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
                },
                events: {
                    show: self._updateSelection.bind(self)
                }
            };
            if (self.options.qtipConstructor) {
                self.options.qtipConstructor(element, qtipOptions);
            } else {
                element.qtip(qtipOptions);
            }
        },

        _createTableRow: function() {
            return $('<tr>', {height: 13});
        },

        _updateSelection: function() {
            var selectedColor = this.options.selectedColor;
            this._paletteTable.find('.palette-color').each(function() {
                var $this = $(this);
                var color = $this.data('color');
                if (selectedColor !== null
                        && color.background === selectedColor.background
                        && color.text === selectedColor.text) {
                    $this.addClass('selected');
                } else {
                    $this.removeClass('selected');
                }
            });
        }
    });
})(jQuery);
