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
    $.widget("indico.multitextfield", {

        options: {
            fieldsCaption: "field",
            parameterManager: undefined,
            parameterType: "text",
            sortable: false,
            valueField: undefined, // A (hidden) field of which the value is a dict of all input fields values
            fieldName: undefined   // String used as a key to an input field value
        },

        _create: function() {
            this.info = [];
            this.valueField = this.options.valueField;
            this.fieldName = this.options.fieldName;
            if (this.valueField) {
                this.field = this.valueField;
                this.data = this.field.val() ? JSON.parse(this.field.val()) : [];
            }

            this.element.addClass("multi-text-fields");
            this._createList();
            this._handleEvents();
            this._drawList();
        },

        destroy: function() {
            this.element.off("focusout click keyup propertychange paste");
            this.element.removeClass("multi-text-fields");
            this.list.remove();
        },

        _createList: function() {
            var self = this;
            self.list = $("<ul></ul>");
            self.element.append(self.list);

            if (self.options.sortable) {
                self.list.sortable({
                    axis: "y",
                    containment: "parent",
                    cursor: "move",
                    distance: 10,
                    handle: ".handle",
                    items: "li:not(:last-child)",
                    tolerance: "pointer",
                    start: function(e, ui) {
                        self.start_index = ui.item.index();
                        ui.item.find("input").blur();
                    },
                    update: function(e, ui) {
                        _.move(self.info, self.start_index, ui.item.index());
                        if (self.valueField) {
                            _.move(self.data, self.start_index, ui.item.index());
                            self._updateValueField(self.data);
                        }
                    }
                });
            }
        },

        _handleEvents: function() {
            var self = this;

            self.element.on("focusout", "input", function() {
                self._updateField(this);
                self._drawNewItem();
            });

            self.element.on("click", "a", function(e) {
                e.preventDefault();
                self._deleteItem($(this).closest("li"));
            });

            self.element.on("keyup propertychange paste input", "input", function(e) {

                // Enter
                if (e.type == "keyup" && e.which == 13) {
                    $(this).blur();
                    $(this).parent().next().find("input").focus();
                }

                if (self.valueField && $(this).val().trim()) {
                    var oldDataItem = self.data[$(this).parent().index()];
                    self.data[$(this).parent().index()] = self._updateDataItem($(this).val(), oldDataItem);
                    self._updateValueField(self.data);
                }

                if ($(this).val() === "" && !$(this).prop('required')) {
                    self._deleteNewItem($(this).closest("li"));
                }

                self._drawNewItem();
            });

            self.element.on("keydown", "input", function(e) {
                // ESC
                if (e.which == 27) {
                    e.stopPropagation();
                    var value = self._getField($(this).data("id")).value;
                    $(this).val(value);
                    $(this).blur();
                    $(this).trigger("propertychange");
                }
            });
        },

        _drawList: function() {
            var i = 0;
            var self = this;
            var list = self.list;

            self._reinitList();

            if (self.valueField) {
                for (i = 0; i < self.data.length; ++i) {
                    var obj = {id: i, value: self.data[i][self.fieldName], required: true};
                    list.append(self._item(obj));
                    self.info[i] = obj;
                }
            }
            else {
                for (i = 0; i < self.info.length; ++i) {
                    list.append(self._item(self.info[i]));
                }
            }

            self._drawNewItem();
        },

        _reinitList: function() {
            this.next_id = -1;
            this.new_item = undefined;

            this.list.find("li").each(function() {
                $(this).remove();
            });
        },

        _drawNewItem: function() {
            if (this.new_item === undefined || this.new_item.find("input").val() !== "") {
                this.new_item = this._item(this._addNewFieldInfo());
                this.list.append(this.new_item);
                this.element.scrollTop(this.element[0].scrollHeight);
                this._scrollFix();
            }
        },

        _deleteNewItem: function(item) {
            if (item.next()[0] == this.new_item[0]) {
                if (this.valueField) {
                    this.data.splice(item.index(), 1);
                    this._updateValueField(this.data);
                }
                this._deleteNewFieldInfo();
                this.new_item.remove();
                this.new_item = item;
                this._removeFieldFromPM(item.find("input"));
                this._scrollFix();
            }
        },

        _deleteItem: function(item) {
            if (item[0] != this.new_item[0]) {
                if (this.valueField) {
                    this.data.splice(item.index(), 1);
                    this._updateValueField(this.data);
                }
                var id = item.find("input").data("id");
                var index = this._getFieldIndex(id);
                this.info.splice(index, 1);
                this._removeFieldFromPM(item.find("input"));
                item.remove();
                this._scrollFix();
            }
        },

        _addNewFieldInfo: function() {
            var id = this._nextId();
            var field = {"id": id, "value": ""};
            this.info.push(field);
            return field;
        },

        _deleteNewFieldInfo: function() {
            this._prevId();
            this.info.pop();
        },

        _getField: function(id) {
            for (var i=0; i<this.info.length; ++i) {
                if (this.info[i]["id"] == id) {
                    return this.info[i];
                }
            }

            return undefined;
        },

        _getFieldIndex: function(id) {
            for (var i=0; i<this.info.length; ++i) {
                if (this.info[i]["id"] == id) {
                    return i;
                }
            }

            return undefined;
        },

        _addFieldToPM: function(input) {
            if (this.options.parameterManager !== undefined) {
                var parameterType = this.options.parameterType;
                this.options.parameterManager.remove(input);
                this.options.parameterManager.add(input, parameterType, false);
            }
        },

        _removeFieldFromPM: function(input) {
            if (this.options.parameterManager !== undefined) {
                this.options.parameterManager.remove(input);
            }
        },

        _item: function(field) {
            field = field || this._addNewFieldInfo();

            var id = field["id"];
            var value = field["value"];
            var placeholder = field.required ? '' : $T.gettext('Type to add {0}').format(this.options.fieldsCaption);

            var item = $("<li></li>");

            if (this.options.sortable) {
                item.append($("<span class='handle'></span>"));
            }

            var newInput = $('<input>', {
                type: 'text',
                required: field.required,
                data: {
                    id: id
                },
                value: value,
                placeholder: placeholder
            });

            this._validateValue(newInput);
            item.append(newInput);

            item.append($('<a>', {
                class: 'i-button-remove icon-remove',
                title: $T("Delete"),
                href: '#',
                tabindex: '-1'
            }));

            item.find("a.i-button-remove").qtip({
                position: {
                    at: "top center",
                    my: "bottom center",
                    target: item.find("a")
                },
                hide: {
                    event: "mouseleave"
                }
            });

            return item;
        },

        _updateField: function(input) {
            input = $(input);
            if (input.val() === "" && !input.prop('required')) {
                var item = input.closest("li");
                this._deleteItem(item);
            } else {
                this._getField(input.data("id"))["value"] = input.val();
                this._addFieldToPM(input);
            }
        },

        _nextId: function() {
            return this.next_id--;
        },

        _prevId: function() {
            return this.next_id === 0? this.next_id : this.next_id++;
        },

        _scrollFix: function() {
            if ((this.element[0].clientHeight+1 < this.element[0].scrollHeight)) {
                this.element.find("input").addClass("width-scrolling");
            } else {
                this.element.find("input").removeClass("width-scrolling");
            }
        },

        getInfo: function() {
            return this.info.slice().splice(0, this.info.length-1);
        },

        setInfo: function(info) {
            this.info = info;
            this._drawList();
        },

        _updateValueField: function(newData) {
            this.field.val(JSON.stringify(newData)).trigger('change');
            this.data = newData;
        },

        _updateDataItem: function(value, oldDataItem) {
            if (!oldDataItem) {
                oldDataItem = {};
            }
            oldDataItem[this.fieldName] = value;
            return oldDataItem;
        },

        _validateValue: function(field) {
            if ('setCustomValidity' in field[0]) {
                field.on('change input', function() {
                    if (!field.val() || field.val().trim()) {
                        field[0].setCustomValidity('');
                    } else {
                        field[0].setCustomValidity($T('Empty values are not allowed.'));
                    }
                });
            }
        }
    });
})(jQuery);
