// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {$T} from 'indico/utils/i18n';

(function($) {
  function move(array, fromIndex, toIndex) {
    array.splice(toIndex, 0, array.splice(fromIndex, 1)[0]);
    return array;
  }

  $.widget('indico.multitextfield', {
    options: {
      fieldsCaption: 'field',
      parameterManager: undefined,
      parameterType: 'text',
      sortable: false,
      valueField: undefined, // A (hidden) field of which the value is a dict of all input fields values
      fieldName: undefined, // String used as a key to an input field value
    },

    _create() {
      this.info = [];
      this.valueField = this.options.valueField;
      this.fieldName = this.options.fieldName;
      if (this.valueField) {
        this.field = this.valueField;
        this.data = this.field.val() ? JSON.parse(this.field.val()) : [];
      }

      this.element.addClass('multi-text-fields');
      this._createList();
      this._handleEvents();
      this._drawList();
    },

    destroy() {
      this.element.off('focusout click keyup propertychange paste');
      this.element.removeClass('multi-text-fields');
      this.list.remove();
    },

    _createList() {
      const self = this;
      self.list = $('<ul></ul>');
      self.element.append(self.list);

      if (self.options.sortable) {
        self.list.sortable({
          axis: 'y',
          containment: 'parent',
          cursor: 'move',
          distance: 10,
          handle: '.handle',
          items: 'li:not(:last-child)',
          tolerance: 'pointer',
          start(e, ui) {
            self.start_index = ui.item.index();
            ui.item.find('input').blur();
          },
          update(e, ui) {
            move(self.info, self.start_index, ui.item.index());
            if (self.valueField) {
              move(self.data, self.start_index, ui.item.index());
              self._updateValueField(self.data);
            }
          },
        });
      }
    },

    _handleEvents() {
      const self = this;

      self.element.on('focusout', 'input', function() {
        self._updateField(this);
        self._drawNewItem();
      });

      self.element.on('click', 'a', function(e) {
        e.preventDefault();
        self._deleteItem($(this).closest('li'));
      });

      self.element.on('keyup propertychange paste input', 'input', function(e) {
        // Enter
        if (e.type === 'keyup' && e.which === 13) {
          $(this).blur();
          $(this).parent().next().find('input').focus();
        }

        if (self.valueField && $(this).val().trim()) {
          const oldDataItem = self.data[$(this).parent().index()];
          self.data[$(this).parent().index()] = self._updateDataItem($(this).val(), oldDataItem);
          self._updateValueField(self.data);
        }

        if ($(this).val() === '' && !$(this).prop('required')) {
          self._deleteNewItem($(this).closest('li'));
        }

        self._drawNewItem();
      });

      self.element.on('keydown', 'input', function(e) {
        // ESC
        if (e.which === 27) {
          e.stopPropagation();
          const value = self._getField($(this).data('id')).value;
          $(this).val(value);
          $(this).blur();
          $(this).trigger('propertychange');
        }
      });
    },

    _drawList() {
      let i = 0;
      const self = this;
      const list = self.list;

      self._reinitList();

      if (self.valueField) {
        for (i = 0; i < self.data.length; ++i) {
          const obj = {id: i, value: self.data[i][self.fieldName], required: true};
          list.append(self._item(obj));
          self.info[i] = obj;
        }
      } else {
        for (i = 0; i < self.info.length; ++i) {
          list.append(self._item(self.info[i]));
        }
      }

      self._drawNewItem();
    },

    _reinitList() {
      this.next_id = -1;
      this.new_item = undefined;

      this.list.find('li').each(function() {
        $(this).remove();
      });
    },

    _drawNewItem() {
      if (this.new_item === undefined || this.new_item.find('input').val() !== '') {
        this.new_item = this._item(this._addNewFieldInfo());
        this.list.append(this.new_item);
        this.element.scrollTop(this.element[0].scrollHeight);
        this._scrollFix();
      }
    },

    _deleteNewItem(item) {
      if (item.next()[0] === this.new_item[0]) {
        if (this.valueField) {
          this.data.splice(item.index(), 1);
          this._updateValueField(this.data);
        }
        this._deleteNewFieldInfo();
        this.new_item.remove();
        this.new_item = item;
        this._removeFieldFromPM(item.find('input'));
        this._scrollFix();
      }
    },

    _deleteItem(item) {
      if (item[0] !== this.new_item[0]) {
        if (this.valueField) {
          this.data.splice(item.index(), 1);
          this._updateValueField(this.data);
        }
        const id = item.find('input').data('id');
        const index = this._getFieldIndex(id);
        this.info.splice(index, 1);
        this._removeFieldFromPM(item.find('input'));
        item.remove();
        this._scrollFix();
      }
    },

    _addNewFieldInfo() {
      const id = this._nextId();
      const field = {id, value: ''};
      this.info.push(field);
      return field;
    },

    _deleteNewFieldInfo() {
      this._prevId();
      this.info.pop();
    },

    _getField(id) {
      for (let i = 0; i < this.info.length; ++i) {
        if (this.info[i]['id'] === id) {
          return this.info[i];
        }
      }

      return undefined;
    },

    _getFieldIndex(id) {
      for (let i = 0; i < this.info.length; ++i) {
        if (this.info[i]['id'] === id) {
          return i;
        }
      }

      return undefined;
    },

    _addFieldToPM(input) {
      if (this.options.parameterManager !== undefined) {
        const parameterType = this.options.parameterType;
        this.options.parameterManager.remove(input);
        this.options.parameterManager.add(input, parameterType, false);
      }
    },

    _removeFieldFromPM(input) {
      if (this.options.parameterManager !== undefined) {
        this.options.parameterManager.remove(input);
      }
    },

    _item(field) {
      field = field || this._addNewFieldInfo();

      const id = field['id'];
      const value = field['value'];
      const placeholder = field.required
        ? ''
        : $T.gettext('Type to add {0}').format(this.options.fieldsCaption);

      const item = $('<li></li>');

      if (this.options.sortable) {
        item.append($("<span class='handle'></span>"));
      }

      const newInput = $('<input>', {
        type: 'text',
        required: field.required,
        data: {
          id,
        },
        value,
        placeholder,
      });

      this._validateValue(newInput);
      item.append(newInput);

      item.append(
        $('<a>', {
          class: 'i-button-remove icon-remove',
          title: $T('Delete'),
          href: '#',
          tabindex: '-1',
        })
      );

      item.find('a.i-button-remove').qtip({
        position: {
          at: 'top center',
          my: 'bottom center',
          target: item.find('a'),
        },
        hide: {
          event: 'mouseleave',
        },
      });

      return item;
    },

    _updateField(input) {
      input = $(input);
      if (input.val() === '' && !input.prop('required')) {
        const item = input.closest('li');
        this._deleteItem(item);
      } else {
        this._getField(input.data('id'))['value'] = input.val();
        this._addFieldToPM(input);
      }
    },

    _nextId() {
      return this.next_id--;
    },

    _prevId() {
      return this.next_id === 0 ? this.next_id : this.next_id++;
    },

    _scrollFix() {
      if (this.element[0].clientHeight + 1 < this.element[0].scrollHeight) {
        this.element.find('input').addClass('width-scrolling');
      } else {
        this.element.find('input').removeClass('width-scrolling');
      }
    },

    getInfo() {
      return this.info.slice().splice(0, this.info.length - 1);
    },

    setInfo(info) {
      this.info = info;
      this._drawList();
    },

    _updateValueField(newData) {
      this.field.val(JSON.stringify(newData)).trigger('change');
      this.data = newData;
    },

    _updateDataItem(value, oldDataItem) {
      if (!oldDataItem) {
        oldDataItem = {};
      }
      oldDataItem[this.fieldName] = value;
      return oldDataItem;
    },

    _validateValue(field) {
      if ('setCustomValidity' in field[0]) {
        field.on('change input', () => {
          if (!field.val() || field.val().trim()) {
            field[0].setCustomValidity('');
          } else {
            field[0].setCustomValidity($T('Empty values are not allowed.'));
          }
        });
      }
    },
  });
})(jQuery);
