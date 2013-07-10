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
            fields_caption: "field"
        },

        _create: function() {
            var self = this;

            self.info = {};
            self.info["next_index"] = 2;

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

            self.element.on("keyup propertychange paste", "input", function(e) {
                // Enter
                if (e.type == "keyup" && e.which == 13) {
                    $(this).blur();
                }

                if ($(this).val() === "") {
                    self._deleteInput($(this).closest("tr"));
                }

                self._drawInput();
            });

            self.element.on("keydown", "input", function(e) {
                // ESC
                if (e.which == 27) {
                    e.stopPropagation();
                    value = self.info[$(this).data("id")];
                    $(this).val(value);
                    $(this).blur();
                }
            });
        },

        _drawTable: function() {
            var self = this;
            var table = self.table;

            table.find("tr").each(function() {
                $(this).remove();
            });

            for (var key in self.info) {
                if (!isNaN(key)) {
                    table.append(self._row(key));
                }
            }

            self._drawInput();
        },

        _drawInput: function() {
            // if (this.new_row === undefined || this.new_row.data("removed") || this.new_row.find("input").val() !== "") {
            if (this.new_row === undefined || this.new_row.find("input").val() !== "") {
                this.new_row = this._row();
                this.table.append(this.new_row);
                this.element.scrollTop(this.element[0].scrollHeight);
            }
        },

        _deleteInput: function(row) {
            if (row.next()[0] == this.new_row[0]) {
                this._fixIndex();
                this.new_row.remove();
                this.new_row = row;
            }
        },

        destroy: function() {
            // TODO: destroy
        },

        _deleteRow: function(row) {
            if (row[0] != this.new_row[0]) {
                var id = $(this).closest("tr").find("input").data("id");
                delete this.info[id];
                row.remove();
            }
        },

        _fixIndex: function() {
            this.info["next_index"]--;
        },

        _nextIndex: function() {
            return this.info["next_index"]++;
        },

        _row: function(id) {
            var value;
            var placeholder = "Type to add " + this.options["fields_caption"];

            if (id !== undefined) {
                value = this.info[id];
            } else {
                id = this._nextIndex();
                value = "";
            }

            var row = $("<tr></tr>");
            var dragger = $("<td class='dragger'>.</td>");
            var field = $("<td><input class='input-text' type='text' data-id='"+ id +"' placeholder='"+ placeholder+"' value='"+ value +"'/></td>");
            var remove = $("<td><a class='i-small-button icon-remove' href='#'></a></td>");

            return row.append(dragger).append(field).append(remove);
        },

        _updateField: function(input) {
            input = $(input);
            var row = input.closest("tr");
            if (input.val() === "") {
                this._deleteRow(row);
            } else {
                this.info[input.data("id")] = input.val();
            }
        },

        getInfo: function() {
            return this.info;
        },

        setInfo: function(info) {
            this.info = info;
            _drawTable();
        }
    });
})(jQuery);