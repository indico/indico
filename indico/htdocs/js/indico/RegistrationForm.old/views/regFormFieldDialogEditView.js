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

var RegFormFieldsEditView = Backbone.View.extend({

    events : {
        'click .nav-tabs li a' :    'tabManager',
        'click .addItem'       :    'addItem',
        'click .sortItem'      :    'sortRow',
        'submit form'          :    'submitForm'
    },

    initialize: function(el, model){
        var self = this;

        this.model = model;
        $(this.el).dialog({
            modal: true,
            autoOpen: false,
            resizable: false,
            width : 'auto',
            autoResize:true,
            position: ['middle','middle'],
            buttons: {
                Save: function() {
                    if($('form', self.el).checkValidity()) {
                        if(self.fieldId == 'isNew') {
                            self.commitCreate();
                        } else {
                            self.commitUpdate();
                        }
                        self.clean();
                        $(this).dialog('close');
                    } else {
                        alert($T('Correct the errors before saving.'));
                        $('#form-opt-validate').trigger('click');
                    }
                },
                Cancel: function() {
                    self.clean();
                    $(this).dialog('close');
                }
            }
        });
    },

    render: function(sectionId, fieldId, field) {
        this.fieldId = fieldId;
        this.sectionId = sectionId;

        if(fieldId == 'isNew') {
            this.field = field;
        } else {
            this.field = this.model.getSectionById(sectionId).getFieldById(fieldId);
        }

        $(this.el).html(this.getFieldEdit({field: this.field, sectionId: this.sectionId}));
        this.postRender();

        return this;
    },

    postRender: function(){
        $(this.el).dialog('open');
        $('#radio').buttonset();
        // Cleaning
        delete this.tableView;
    },

    commitUpdate: function(){
        var data = {};
        data.sectionId = this.sectionId;
        data.fieldId = this.fieldId;
        if (this.tableView) {
            var itemsData = $.extend(true, {}, data);
            itemsData.items = this.tableView.toJSON();
            this.model.getSectionById(this.sectionId).setFieldItems(itemsData);
        }
        var updateFieldData = toDict($('#optionsForm').serializeArray());
        data.updateFieldData = updateFieldData;
        this.model.getSectionById(this.sectionId).updateField(data);
    },

    commitCreate: function(){
        var field =  toDict($('#optionsForm').serializeArray());
        field.input = this.field.input;
        if (this.tableView) {
            field.radioitems = this.tableView.toJSON();
        }
        this.model.getSectionById(this.sectionId).createField({field : field});
    },

    addItem: function(event, ui){
        event.preventDefault();
        var newRowData = {
                id : 'isNew',
                caption : '',
                billable : false,
                price : '',
                placesLimit : '0',
                isEnabled : true
        };
        this.tableView.addRow(newRowData);
    },

    sortRow: function(event, ui){
        event.preventDefault();
        this.tableView.sortRow('asc','caption');
    },

    tabManager: function(event, ui) {
        $('.active',this.el).removeClass('active');
        $(event.target).parent('li').addClass('active');
        var tabDiv = $(event.target).attr('ref');
        $(tabDiv).addClass('active');
        if( $(event.target).attr('id') == 'tab-editItems' ) {
            this.showTableItem();
        }
    },

    showTableItem: function(){
        var self = this;
        if ( typeof this.fieldItemView == 'undefined' ){
            this.fieldItemView = new RadioFieldModel( this.field.values );
            this.tableView = new EditionTable(this.fieldItemView, $('#editionTable'));
        }
    },

    getFieldEdit: function(dict) {
        dict.field.disabled = $.inArray(dict.field.lock, "mandatory");
        return nunenv.render("regFormFieldEdit.tpl", dict);
    },

    submitForm: function(event) {
        event.preventDefault();
    },

    clean: function(){
        delete this.fieldItemView;
        delete this.tableView;
    }
});
