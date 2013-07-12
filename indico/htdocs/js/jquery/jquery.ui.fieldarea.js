/*
* -*- mode: text; coding: utf-8; -*-


   This file is part of Indico.
   Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).

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
            parameter_type: "text"
        },

        _create: function() {
            var self = this;

            self.info = [];
            self.next_index = -1;

            self.table = $("<table></table>");
            self.element.addClass("field-area scrollable");
            self.element.append(self.table);

            self._handleEvents();
            self._drawTable();
        },

        _handleEvents: function() {
            var self = this;

            self.element.on("focusout", "input", function(e) {
                self._updateField(this);
            });

            self.element.on("click", "a", function(e) {
                e.preventDefault();
                self._deleteRow($(this).closest("tr"));
            });

            self.element.on("keyup propertychange paste change", "input", function(e) {
                // Enter
                if (e.type == "keyup" && e.which == 13) {
                    $(this).blur();
                }

                if ($(this).val() === "") {
                    self._deleteNewInput($(this).closest("tr"));
                }

                self._drawNewInput();
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

        _drawTable: function() {
            var self = this;
            var table = self.table;

            self._reinitTable();

            for (var i=0; i<self.info.length; ++i) {
                table.append(self._row(self.info[i]));
            }

            self._drawNewInput();
        },

        _reinitTable: function() {
            this.next_index = -1;
            this.new_row = undefined;

            this.table.find("tr").each(function() {
                $(this).remove();
            });
        },

        _drawNewInput: function() {
            if (this.new_row === undefined || this.new_row.find("input").val() !== "") {
                this.new_row = this._row(this._addNewField());
                this.table.append(this.new_row);
                this.element.scrollTop(this.element[0].scrollHeight);
            }
        },

        _deleteNewInput: function(row) {
            if (row.next()[0] == this.new_row[0]) {
                this._deleteNewField();
                this.new_row.remove();
                this.new_row = row;
                this._removeFromPM(row.find("input"));
            }
        },

        destroy: function() {
            this.element.off("focusout click keyup propertychange paste");
            this.element.removeClass("field-area scrollable");
            this.table.remove();
        },

        _deleteRow: function(row) {
            if (row[0] != this.new_row[0]) {
                var id = row.find("input").data("id");
                var index = this._getFieldIndex(id);
                this.info.splice(index, 1);
                this._removeFromPM(row.find("input"));
                row.remove();
            }
        },

        _addNewField: function() {
            var id = this._nextIndex();
            var field = {"id": id, "value": ""};
            this.info.push(field);
            return field;
        },

        _deleteNewField: function() {
            this.prevIndex();
            this.info.pop();
        },

        _nextIndex: function() {
            return this.next_index--;
        },

        _prevIndex: function() {
            return this.next_index === 0? this.next_index : this.next_index++;
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

        _addToPM: function(input) {
            if (this.options["parameter_manager"] !== undefined) {
                var parameter_type = this.options["parameter_type"];
                this.options["parameter_manager"].remove(input);
                this.options["parameter_manager"].add(input, parameter_type, false);
            }
        },

        _removeFromPM: function(input) {
            if (this.options["parameter_manager"] !== undefined) {
                this.options["parameter_manager"].remove(input);
            }
        },

        _row: function(field) {
            field = field || this._addNewField();

            var id = field["id"];
            var value = field["value"];
            var placeholder = "Type to add " + this.options["fields_caption"];

            var row = $("<tr></tr>")
                        .append($("<td class='dragger'>.</td>"))
                        .append($("<td><input class='input-text' type='text' data-id='"+ id +"' placeholder='"+ placeholder+"' value='"+ value +"'/></td>"))
                        .append($("<td><a class='i-small-button icon-remove' href='#'></a></td>"));

            return row;
        },

        _updateField: function(input) {
            input = $(input);
            if (input.val() === "") {
                var row = input.closest("tr");
                this._deleteRow(row);
            } else {
                this._getField(input.data("id"))["value"] = input.val();
                this._addToPM(input);
            }
        },

        getInfo: function() {
            this._cleanInfo();
            return this.info;
        },

        _cleanInfo: function() {
            if (this.info[this.info.length-1]["value"] === "") {
                this.info.pop();
            }
        },

        setInfo: function(info) {
            this.info = info;
            this._drawTable();
        }
    });
})(jQuery);
