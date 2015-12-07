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
            var palette = $('<div>', {'class': 'color-palette'});
            var paletteTable = $('<table>');
            var availableColors = this.options.availableColors;
            var tr = this._createTableRow();

            for (var i = 0; i < availableColors.length; ++i) {
                var uniqueId = _.uniqueId('palette-color');
                var td = $('<td>', {
                    'css': {'background': '#' + availableColors[i].background},
                    'class': 'palette-color',
                    'id': uniqueId
                });

                $(document).on('click', '#' + uniqueId, function(evt) {
                    evt.preventDefault();

                    var $this = $(this),
                        backgroundColor = $this.find('.background-box').data('value'),
                        textColor = $this.find('.text-box').data('value');

                    element.css({'background': backgroundColor, 'color': textColor + ' !important'});

                    if (self.options.onSelect) {
                        self.options.onSelect.call(element, backgroundColor, textColor);
                    }

                    element.qtip('hide');
                });

                var colorBox = $('<div>', {
                    'data-value': '#' + availableColors[i].background,
                    'class': 'background-box'
                });

                colorBox.append($('<div>', {
                    'css': {'background': '#' + availableColors[i].text},
                    'class': 'text-box',
                    'data-value': '#' + availableColors[i].text
                }));

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

            element.qtip({
                prerender: false,
                overwrite: false,
                style: {
                    classes: 'color-palette'
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
                    text: palette.html()
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
