/* This file is part of Indico.
 * Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
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


var EditionTable = Backbone.View.extend({

    initialize: function (model, el, config) {
        this.el = el;
        this.model = model;
        // if undefined default location in the model
        if (typeof config == 'undefined'){
            this.config = this.model.editTableConfig;
        } else {
            this.config = config;
        }
        this.render();
        var removeRow = _.bind(this.removeRow, this);
        $(".actionTrash").live("click", removeRow);
    },

    render: function () {
        var self = this;
        var data = this.model.get(this.config.data);
        $(this.el).html(this.getTpl('table', { config : this.config, data : data }));
        _.each(data, function(item, item_ind){
            var cond = true;
            if (typeof self.config.displayCond != 'undefined'){
                cond = self.config.displayCond(item);
            }
            if (cond === true) {
                $('table',self.el).append(self.getTpl('row', {config : self.config, item : item}));
            }
        });
        this.postRender();
    },

    appendRender: function (rowHTML) {
        $('table',this.el).append(rowHTML);
        this.postRender();
    },

    postRender: function () {
        $( ".actionTrash" ).button({
            icons: { primary: "ui-icon-trash" },
            text: false
        });
        var actions = this.config.actions;
        if (actions.indexOf("sortable") > -1) {
            $(this.el).sortable({ items: 'tbody', axis : "y" });
        }
    },

    removeRow: function ( event, ui ) {
        rep = confirm($T('Are you sure you want to disable this field ?\nThis action is irreversible.'));
        if(rep === true) {
            $(event.target).closest("tr").data('remove', true);
            $(event.target).closest("tr").fadeOut('slow');
        }
    },

    addRow: function(item){
        var rowHTML = this.getTpl('row', { config : this.config, item : item });
        this.appendRender(rowHTML);
    },

    sortRow: function(type, col){
        var self = this;
        var rows = $('tbody', this.el);
        rows.sort(function(a, b){
            var keyA = $('td [name=\'' + col + '\']', a).val();
            var keyB = $('td [name=\'' + col + '\']', b).val();
            if(type == 'asc'){
                return (keyA > keyB) ? 1 : 0;
            } else {
                return (keyA < keyB) ? 1 : 0;
            }
        });
        $.each(rows, function(index, row){
            self.appendRender(row);
        });
    },

    toJSON: function () {
        var self = this;
        var json = [];
        $("table tr", this.el).each( function ( i, el ) {
            if( $(el).attr('role') == "row" ) {
                var dict = { id : $(el).attr('id') };
                $( el ).children("td").each( function ( j, entry ) {
                    var val = $(entry).find("input[type=text],textarea,select,input[type=radio]").val();
                    if (val === null) {
                        val='';
                    }
                    dict[$(entry).attr('name')] = val;
                });
                if ( $(el).data('remove') ){
                    dict.remove = true;
                }
                json.push(dict);
            }
        });
        return json;
    },

    getTpl: function( tplId, dict ) {
        var tpl = TemplateManager.getSync('RegistrationForm','editionTable', tplId);
        return _.template(tpl, dict);
    }
});
