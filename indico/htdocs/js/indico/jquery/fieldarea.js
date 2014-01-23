/*
* -*- mode: text; coding: utf-8; -*-


   This file is part of Indico.
   Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).

   Indico is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation; either version 3 of the
   License, or (at your option) any later version.

   Indico is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with Indico; if not, see <http://www.gnu.org/licenses/>.
*/

(function($) {
    $.widget("ui.fieldarea", {

        options: {
            fields_caption: "field",
            parameter_manager: undefined,
            parameter_type: "text",
            ui_sortable: false
        },

        _create: function() {
            this.info = [];

            this.element.addClass("field-area");
            this._createList();
            this._handleEvents();
            this._drawList();
        },

        destroy: function() {
            this.element.off("focusout click keyup propertychange paste");
            this.element.removeClass("field-area");
            this.list.remove();
        },

        _createList: function() {
            var self = this;
            self.list = $("<ul></ul>");
            self.element.append(self.list);

            if (self.options["ui_sortable"]) {
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
                    }
                });
            }
        },

        _handleEvents: function() {
            var self = this;

            self.element.on("focusout", "input", function(e) {
                self._updateField(this);
                self._drawNewItem();
            });

            self.element.on("click", "a", function(e) {
                e.preventDefault();
                self._deleteItem($(this).closest("li"));
            });

            self.element.on("keyup propertychange paste", "input", function(e) {

                // Enter
                if (e.type == "keyup" && e.which == 13) {
                    $(this).blur();
                    $(this).parent().next().find("input").focus();
                }

                if ($(this).val() === "") {
                    self._deleteNewItem($(this).closest("li"));
                }

                self._drawNewItem();
            });

            self.element.on("keydown", "input", function(e) {
                // ESC
                if (e.which == 27) {
                    e.stopPropagation();
                    value = self._getField($(this).data("id"))["value"];
                    $(this).val(value);
                    $(this).blur();
                    $(this).trigger("propertychange");
                }
            });
        },

        _drawList: function() {
            var self = this;
            var list = self.list;

            self._reinitList();

            for (var i=0; i<self.info.length; ++i) {
                list.append(self._item(self.info[i]));
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
                this._deleteNewFieldInfo();
                this.new_item.remove();
                this.new_item = item;
                this._removeFieldFromPM(item.find("input"));
                this._scrollFix();
            }
        },

        _deleteItem: function(item) {
            if (item[0] != this.new_item[0]) {
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
            if (this.options["parameter_manager"] !== undefined) {
                var parameter_type = this.options["parameter_type"];
                this.options["parameter_manager"].remove(input);
                this.options["parameter_manager"].add(input, parameter_type, false);
            }
        },

        _removeFieldFromPM: function(input) {
            if (this.options["parameter_manager"] !== undefined) {
                this.options["parameter_manager"].remove(input);
            }
        },

        _item: function(field) {
            field = field || this._addNewFieldInfo();

            var id = field["id"];
            var value = field["value"];
            var placeholder = "Type to add " + this.options["fields_caption"];

            var item = $("<li></li>");

            if (this.options["ui_sortable"]) {
                item.append($("<span class='handle'></span>"));
            }

            item.append($("<input type='text' data-id='"+ id +"' placeholder='"+ placeholder+"' value='"+ value +"'/>").placeholder())
                .append($("<a class='i-button-remove' title='"+ $T("Delete") +"' href='#' tabIndex='-1'><i class='icon-remove'></i></a>"));

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
            if (input.val() === "") {
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
        }
    });
})(jQuery);
