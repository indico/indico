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
    $.widget('indico.itempicker', {

        options: {
            onSelect: null, // function called every time an item gets selected from the list
            checkedItemIcon: 'icon-checkmark',
            uncheckedItemIcon: 'icon-stop',
            items: null, // all the options that should be included in the dropdown
            footerElements: null, // list of objects with (title, callback) keys
            containerClasses: '', // extra classes to be applied to the container
            filterPlaceholder: $T.gettext('Type to filter...') // text displayed inside the input field
        },

        _create: function() {
            var items = this.options.items || this.element.data('items') || [];
            var qtipContent = this._createQtipContent(items);

            this.element.qtip({
                prerender: true,
                overwrite: false,
                style: {
                    classes: 'item-picker-qtip ' + this.options.containerClasses
                },
                position: {
                    my: 'right top',
                    at: 'left top',
                    target: this.element,
                    adjust: {
                        mouse: false,
                        scroll: false
                    }
                },
                content: {
                    text: qtipContent
                },
                show: {
                    event: 'click',
                    solo: true
                },
                hide: {
                    event: 'unfocus click'
                },
                events: {
                    show: function() {
                        _.defer(function() {
                            qtipContent.find('.filter-input').focus();
                        });
                    }
                }
            });
        },

        _destroy: function() {
            self.element.qtip('destroy');
        },

        _createQtipContent: function(items) {
            var self = this;
            var dropdownContainer = $('<div>', {'class': 'dropdown-container'});
            var filterWrapper = $('<div>', {'class': 'dropdown-filter-wrapper'});
            var filterInput = $('<input>', {'type': 'text', 'class': 'filter-input',
                                            'attr': {'placeholder': self.options.filterPlaceholder}});
            var itemsContainer = $('<div>', {'class': 'dropdown-items-container'});

            function handleInput() {
                var textTyped = filterInput.val().trim().toLowerCase();

                dropdownContainer.find('.dropdown-item').each(function() {
                    var $item = $(this);
                    var found = $item.data('filter').toLowerCase().indexOf(textTyped) !== -1;

                    $item.toggle(found);
                });
            }

            filterWrapper.append(filterInput);
            $(window).load(function() {
                filterInput.clearableinput({'onInput': handleInput, 'onClear': handleInput, 'focusOnStart': true});
            });

            dropdownContainer.append(filterWrapper);
            $.each(items, function(index, itemData) {
                var isSelected = (itemData.id === self.element.data('selected-item-id'));
                var itemIcon = $('<span>', {'class': 'item-icon ' + self.options.uncheckedItemIcon});
                var $item = $('<div>', {
                    'class': 'dropdown-item',
                    'data': {'filter': itemData.title},
                    'on': {
                        'click': function() {
                            self.element.qtip('hide');
                            if (itemData.id === self.element.data('selected-item-id')) {
                                self._handleClear($item, itemData);
                            } else {
                                self._handleSelect($item, itemData);
                            }
                        }
                    }
                });

                if (itemData.colors) {
                    itemIcon.css('color', '#' + itemData.colors.background);
                }

                $item.append($('<span>', {'class': self.options.checkedItemIcon + ' active-item-icon'}));
                $item.append(itemIcon).append($('<span>', {'class': 'item-title', 'text': itemData.title}));

                if (isSelected) {
                    self._markItemAsSelected($item, itemData);
                    itemsContainer.prepend($item);
                } else {
                    itemsContainer.append($item);
                }
            });

            dropdownContainer.append(itemsContainer);
            if (self.options.footerElements) {
                self._appendFooterItems(dropdownContainer);
            }

            return dropdownContainer;
        },

        refreshItemList: function(items) {
            this.element.qtip('option', 'content.text', this._createQtipContent(items));
        },

        hide: function() {
            this.element.qtip('hide');
        },

        _handleSelect: function(item, itemData) {
            var promise;
            var self = this;

            if ($.isFunction(self.options.onSelect)) {
                promise = self.options.onSelect.call(self.element, itemData);
            }
            if (promise === undefined) {
                promise = $.Deferred().resolve();
            }

            return promise.then(function() {
                self.element.data('selected-item-id', itemData.id);
                self._markItemAsSelected(item, itemData);
            });
        },

        _markItemAsSelected: function(item, itemData) {
            var itemsContainer = item.closest('.dropdown-items-container');
            itemsContainer.find('.dropdown-item').css('background', '').removeClass('active');
            itemsContainer.find('.item-title').css('color', '');
            item.addClass('active');
            if (itemData.colors) {
                item.css('background', '#' + this._increaseBrightness(itemData.colors.background, 50));
                item.find('.item-title').css('color', '#' + this._getContrastYIQ(itemData.colors.background));
            }
        },

        _deselectItem: function(item) {
            item.css('background', '').removeClass('active').find('.item-title').css('color', '');
        },

        _increaseBrightness: function(hex, percent) {
            // from http://stackoverflow.com/questions/6443990/javascript-calculate-brighter-colour
            // strip the leading # if it's there
            hex = hex.trim().replace(/^#/, '');

            // convert 3 char codes --> 6, e.g. `E0F` --> `EE00FF`
            if (hex.length == 3) {
                hex = hex.replace(/(.)/g, '$1$1');
            }

            var r = parseInt(hex.substr(0, 2), 16),
                g = parseInt(hex.substr(2, 2), 16),
                b = parseInt(hex.substr(4, 2), 16);

            return ((0 | (1 << 8) + r + (256 - r) * percent / 100).toString(16)).substr(1) +
                   ((0 | (1 << 8) + g + (256 - g) * percent / 100).toString(16)).substr(1) +
                   ((0 | (1 << 8) + b + (256 - b) * percent / 100).toString(16)).substr(1);
        },

        _getContrastYIQ: function(hexcolor) {
            var r = parseInt(hexcolor.substr(0, 2), 16);
            var g = parseInt(hexcolor.substr(2, 2), 16);
            var b = parseInt(hexcolor.substr(4, 2), 16);
            var yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
            return (yiq >= 128) ? '000' : 'FFF';
        },

        _handleClear: function(item, itemData) {
            var promise;
            var self = this;

            if ($.isFunction(this.options.onClear)) {
                promise = this.options.onClear.call(this.element, itemData);
            }

            if (promise === undefined) {
                promise = $.Deferred().resolve();
            }

            return promise.then(function() {
                self.element.data('selected-item-id', '');
                self._deselectItem(item);
            });
        },

        _appendFooterItems: function(container) {
            var self = this;
            var footerElements = self.options.footerElements;

            container.append($('<div>', {'class': 'divider'}));
            $.each(footerElements, function() {
                var $this = this;
                var actionButton = $('<div>', {
                    'class': 'action-button',
                    'text': $this.title,
                    'on': {
                        'click': function() {
                            self.element.qtip('hide');
                            if ($.isFunction($this.onClick)) {
                                $this.onClick.call(actionButton);
                            }
                        }
                    }
                });

                container.append(actionButton);
            });
        }
    });
})(jQuery);
