// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

import {natSortCompare} from 'indico/utils/sort';

import {$T} from '../../utils/i18n';

(function($) {
  $.widget('indico.itempicker', {
    options: {
      onSelect: null, // function called every time an item gets selected from the list
      checkedItemIcon: 'icon-checkmark',
      uncheckedItemIcon: 'icon-stop',
      items: null, // all the options that should be included in the dropdown
      footerElements: null, // list of objects with (title, callback) keys
      containerClasses: '', // extra classes to be applied to the container
      filterPlaceholder: $T.gettext('Type to filter...'), // text displayed inside the input field
    },

    _create() {
      this.selectedItem = null;
      this._createItemsDict(this.options.items || this.element.data('items') || []);

      const qbubbleContent = this._createQbubbleContent(this.itemsDict);

      this.element.qbubble({
        prerender: true,
        show: {
          ready: true,
        },
        content: {
          text: qbubbleContent,
        },
        style: {
          classes: 'item-picker-qbubble {0}'.format(this.options.containerClasses),
        },
        position: {
          my: 'right top',
          at: 'left top',
        },
        events: {
          show: this._filter(qbubbleContent),
        },
      });
    },

    _filter(qbubbleContent) {
      _.defer(() => {
        function handleInput() {
          const $this = $(this);
          const textTyped = $this.val().trim().toLowerCase();
          const dropdownContainer = $this.closest('.dropdown-container');
          dropdownContainer.find('.dropdown-item').each(function() {
            const $item = $(this);
            const found = $item.data('filter').toLowerCase().indexOf(textTyped) !== -1;
            $item.toggle(found);
          });
        }
        qbubbleContent
          .find('.filter-input')
          .clearableinput({onInput: handleInput, onClear: handleInput, focusOnStart: true})
          .focus();
      });
    },

    _destroy() {
      self.element.qbubble('destroy');
    },

    _createItemsDict(items) {
      const self = this;
      this.itemsDict = {};

      $.each(items, (index, data) => {
        self.itemsDict[data.id] = {data, elem: null};
      });
    },

    _createQbubbleContent(items) {
      const self = this;
      const dropdownContainer = $('<div>', {class: 'dropdown-container'});
      const filterWrapper = $('<div>', {class: 'dropdown-filter-wrapper'});
      const filterInput = $('<input>', {
        type: 'text',
        class: 'filter-input',
        attr: {placeholder: self.options.filterPlaceholder},
      });
      const itemsContainer = $('<div>', {class: 'dropdown-items-container'});

      filterWrapper.append(filterInput);
      dropdownContainer.append(filterWrapper);

      $.each(items, (itemId, itemDict) => {
        const isSelected = +itemId === +self.element.data('selected-item-id');
        const itemData = itemDict.data;
        const itemIcon = $('<span>', {class: `item-icon ${self.options.uncheckedItemIcon}`});

        const $item = (itemDict.elem = $('<div>', {
          class: 'dropdown-item',
          data: {filter: itemData.title, id: itemId},
          on: {
            click() {
              self.hide();

              if (self.selectedItem && +itemId === +self.selectedItem.id) {
                self._handleSelect($item, null, itemData);
              } else {
                self._handleSelect($item, itemData, self.selectedItem);
              }
            },
          },
        }));

        if (itemData.colors) {
          itemIcon.css('color', `#${itemData.colors.background}`);
        }

        $item.append($('<span>', {class: `${self.options.checkedItemIcon} active-item-icon`}));
        $item.append(itemIcon).append($('<span>', {class: 'item-title', text: itemData.title}));

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

    updateItemList(items) {
      this._createItemsDict(items);
      const qbubbleContent = this._createQbubbleContent(this.itemsDict);
      this.element.qbubble('option', 'content.text', qbubbleContent);
      this.element.qbubble('option', 'show', this._filter(qbubbleContent));
    },

    selectItem(id) {
      const newItem = id !== null ? this.itemsDict[id].data : null;
      const newElem = this.itemsDict[id !== null ? id : this.selectedItem.id].elem;

      this._handleSelect(newElem, newItem, this.selectedItem);
    },

    hide() {
      this.element.qbubble('hide');
    },

    _handleSelect(newElem, newItem, oldItem) {
      let promise;
      const self = this;

      if ($.isFunction(self.options.onSelect)) {
        promise = self.options.onSelect.call(self.element, newItem, oldItem);
      }
      if (promise === undefined) {
        promise = $.Deferred().resolve();
      }

      return promise.then(() => {
        if (newItem) {
          self._selectItem(newElem, newItem);
        } else {
          self._deselectItem(newElem);
        }
      });
    },

    _selectItem(item, itemData) {
      const itemsContainer = item.closest('.dropdown-items-container');
      const dropdownItems = itemsContainer.find('.dropdown-item');

      dropdownItems.css('background', '').removeClass('active');
      itemsContainer.find('.item-title').css('color', '');
      item.addClass('active');

      if (itemData.colors) {
        item.css('background', `#${this._increaseBrightness(itemData.colors.background, 50)}`);
        item
          .find('.item-title')
          .css('color', `#${this._getContrastYIQ(itemData.colors.background)}`);
      }

      this.selectedItem = itemData;
      this._sortItems(itemsContainer);
    },

    _sortItems(dropdownContainer) {
      const self = this;
      const dropdownItems = dropdownContainer.find('.dropdown-item');

      dropdownItems
        .detach()
        .sort((a, b) => {
          const $a = $(a);
          const $b = $(b);

          if (self.selectedItem && +$a.data('id') === +self.selectedItem.id) {
            return -1;
          }
          if (self.selectedItem && +$b.data('id') === +self.selectedItem.id) {
            return 1;
          }

          return natSortCompare($a.text().toLowerCase(), $b.text().toLowerCase());
        })
        .appendTo(dropdownContainer);
    },

    _deselectItem(item) {
      this.selectedItem = null;
      item.css('background', '').removeClass('active').find('.item-title').css('color', '');
      this._sortItems(item.closest('.dropdown-items-container'));
    },

    _increaseBrightness(hex, percent) {
      // from http://stackoverflow.com/questions/6443990/javascript-calculate-brighter-colour
      // strip the leading # if it's there
      hex = hex.trim().replace(/^#/, '');

      // convert 3 char codes --> 6, e.g. `E0F` --> `EE00FF`
      if (hex.length === 3) {
        hex = hex.replace(/(.)/g, '$1$1');
      }

      const r = parseInt(hex.substr(0, 2), 16);
      const g = parseInt(hex.substr(2, 2), 16);
      const b = parseInt(hex.substr(4, 2), 16);

      // biome-ignore format: more readable
      return (
        // eslint-disable-next-line no-bitwise
        (0 | ((1 << 8) + r + ((256 - r) * percent) / 100)).toString(16).slice(1) +
        // eslint-disable-next-line no-bitwise
        (0 | ((1 << 8) + g + ((256 - g) * percent) / 100)).toString(16).slice(1) +
        // eslint-disable-next-line no-bitwise
        (0 | ((1 << 8) + b + ((256 - b) * percent) / 100)).toString(16).slice(1)
      );
    },

    _getContrastYIQ(hexColor) {
      const r = parseInt(hexColor.substr(0, 2), 16);
      const g = parseInt(hexColor.substr(2, 2), 16);
      const b = parseInt(hexColor.substr(4, 2), 16);
      const yiq = (r * 299 + g * 587 + b * 114) / 1000;
      return yiq >= 128 ? '000' : 'FFF';
    },

    _appendFooterItems(container) {
      const self = this;
      const footerElements = self.options.footerElements;

      container.append($('<div>', {class: 'divider'}));
      $.each(footerElements, function() {
        const $this = this;
        const actionButton = $('<div>', {
          class: 'action-row',
          text: $this.title,
          on: {
            click() {
              self.hide();
              if ($.isFunction($this.onClick)) {
                $this.onClick.call(actionButton, self.element);
              }
            },
          },
        });

        container.append(actionButton);
      });
    },
  });
})(jQuery);
