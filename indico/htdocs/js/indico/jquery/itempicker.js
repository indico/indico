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
            this.selectedItem = null;
            this._createItemsDict(this.options.items || this.element.data('items') || []);

            var qbubbleContent = this._createQbubbleContent(this.itemsDict);

            this.element.qbubble({
                prerender: true,
                show: {
                    ready: true
                },
                content: {
                    text: qbubbleContent
                },
                style: {
                    classes: 'item-picker-qbubble {0}'.format(this.options.containerClasses)
                },
                position: {
                    my: 'right top',
                    at: 'left top'
                },
                events: {
                    show: function() {
                        _.defer(function() {
                            function handleInput() {
                                var $this = $(this);
                                var textTyped = $this.val().trim().toLowerCase();
                                var dropdownContainer = $this.closest('.dropdown-container');

                                dropdownContainer.find('.dropdown-item').each(function() {
                                    var $item = $(this);
                                    var found = $item.data('filter').toLowerCase().indexOf(textTyped) !== -1;

                                    $item.toggle(found);
                                });
                            }

                            qbubbleContent.find('.filter-input')
                                .clearableinput({'onInput': handleInput, 'onClear': handleInput, 'focusOnStart': true})
                                .focus();
                        });
                    }
                }
            });
        },

        _destroy: function() {
            self.element.qbubble('destroy');
        },

        _createItemsDict: function(items) {
            var self = this;
            this.itemsDict = {};

            $.each(items, function(index, data) {
                self.itemsDict[data.id] = {data: data, elem: null};
            });
        },

        _createQbubbleContent: function(items) {
            var self = this;
            var dropdownContainer = $('<div>', {'class': 'dropdown-container'});
            var filterWrapper = $('<div>', {'class': 'dropdown-filter-wrapper'});
            var filterInput = $('<input>', {'type': 'text', 'class': 'filter-input',
                                            'attr': {'placeholder': self.options.filterPlaceholder}});
            var itemsContainer = $('<div>', {'class': 'dropdown-items-container'});

            filterWrapper.append(filterInput);
            dropdownContainer.append(filterWrapper);

            $.each(items, function(itemId, itemDict) {
                var isSelected = (itemId == self.element.data('selected-item-id'));
                var itemData = itemDict.data;
                var itemIcon = $('<span>', {'class': 'item-icon ' + self.options.uncheckedItemIcon});

                var $item = itemDict.elem = $('<div>', {
                    'class': 'dropdown-item',
                    'data': {'filter': itemData.title, 'id': itemId},
                    'on': {
                        'click': function() {
                            self.hide();

                            if (self.selectedItem && itemId == self.selectedItem.id) {
                                self._handleSelect($item, null, itemData);
                            } else {
                                self._handleSelect($item, itemData, self.selectedItem);
                            }
                        }
                    }
                });

                if (itemData.colors) {
                    itemIcon.css('color', '#' + itemData.colors.background);
                }

                $item.append($('<span>', {'class': self.options.checkedItemIcon + ' active-item-icon'}));
                $item.append(itemIcon).append($('<span>', {'class': 'item-title', 'text': itemData.title}));

                itemsContainer.append($item);

                if (isSelected) {
                    self._selectItem($item, itemData);
                }
            });

            dropdownContainer.append(itemsContainer);
            this._sortItems(itemsContainer);

            if (self.options.footerElements) {
                self._appendFooterItems(dropdownContainer);
            }

            return dropdownContainer;
        },

        updateItemList: function(items) {
            this._createItemsDict(items);
            this.element.qbubble('option', 'content.text', this._createQbubbleContent(this.itemsDict));
        },

        selectItem: function(id) {
            var newItem = id !== null ? this.itemsDict[id].data : null;
            var newElem = this.itemsDict[id !== null ? id : this.selectedItem.id].elem;

            this._handleSelect(newElem, newItem, this.selectedItem);
        },

        hide: function() {
            this.element.qbubble('hide');
        },

        _handleSelect: function(newElem, newItem, oldItem) {
            var promise;
            var self = this;

            if ($.isFunction(self.options.onSelect)) {
                promise = self.options.onSelect.call(self.element, newItem, oldItem);
            }
            if (promise === undefined) {
                promise = $.Deferred().resolve();
            }

            return promise.then(function() {
                if (newItem) {
                    self._selectItem(newElem, newItem);
                } else {
                    self._deselectItem(newElem);
                }
            });
        },

        _selectItem: function(item, itemData) {
            var itemsContainer = item.closest('.dropdown-items-container');
            var dropdownItems = itemsContainer.find('.dropdown-item');

            dropdownItems.css('background', '').removeClass('active');
            itemsContainer.find('.item-title').css('color', '');
            item.addClass('active');

            if (itemData.colors) {
                item.css('background', '#' + this._increaseBrightness(itemData.colors.background, 50));
                item.find('.item-title').css('color', '#' + this._getContrastYIQ(itemData.colors.background));
            }

            this.selectedItem = itemData;
            this._sortItems(itemsContainer);
        },

        _sortItems: function(dropdownContainer) {
            var self = this;
            var dropdownItems = dropdownContainer.find('.dropdown-item');

            dropdownItems.detach().sort(function(a, b) {
                var $a = $(a);
                var $b = $(b);

                if (self.selectedItem && $a.data('id') == self.selectedItem.id) return -1;
                if (self.selectedItem && $b.data('id') == self.selectedItem.id) return 1;

                return strnatcmp($a.text().toLowerCase(), $b.text().toLowerCase());
            }).appendTo(dropdownContainer);
        },

        _deselectItem: function(item) {
            this.selectedItem = null;
            item.css('background', '').removeClass('active').find('.item-title').css('color', '');
            this._sortItems(item.closest('.dropdown-items-container'));
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

        _getContrastYIQ: function(hexColor) {
            var r = parseInt(hexColor.substr(0, 2), 16);
            var g = parseInt(hexColor.substr(2, 2), 16);
            var b = parseInt(hexColor.substr(4, 2), 16);
            var yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
            return (yiq >= 128) ? '000' : 'FFF';
        },

        _appendFooterItems: function(container) {
            var self = this;
            var footerElements = self.options.footerElements;

            container.append($('<div>', {'class': 'divider'}));
            $.each(footerElements, function() {
                var $this = this;
                var actionButton = $('<div>', {
                    'class': 'action-row',
                    'text': $this.title,
                    'on': {
                        'click': function() {
                            self.hide();
                            if ($.isFunction($this.onClick)) {
                                $this.onClick.call(actionButton, self.element);
                            }
                        }
                    }
                });

                container.append(actionButton);
            });
        }
    });
})(jQuery);
