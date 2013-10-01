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


var RegFormSectionBaseDialogView = Backbone.View.extend({

    events : {
        'click .nav-tabs li a'      : 'activeTab',
        'click .actionTabSwitch'    : 'tabSwitcher',
        'sumbit form'               : 'submitForm'

    },

    initialize: function(model){
        var self = this;
        _.bindAll(this);
        self.updateItems = false;
        this.model = model;

        $(this.el).dialog({
            modal: true,
            autoOpen: false,
            resizable: false,
            dialogClass : 'regFormSectionEditDialog',
            minWidth : self.model.editTableConfig.width,
            autoResize: false,
            buttons: {
                    Save: function() {
                            self.save();
                            $(this).dialog('close');

                    },
                    Cancel: function() {
                            $(this).dialog('close');
                    }
            }
        });

        this.render();

    },

    render: function(){
        $(this.el).html(this.getSectionEdit('edit-dialog', { section : this.model.toJSON(),
                contentWidth : this.model.editTableConfig.width
            }));
        $('.nav-tabs li:first',this.el).addClass('active');
        $('.tab-content div:first',this.el).addClass('active');
        this.postRender();
    },

    postRender: function(){
        $(this.el).dialog('option', 'position', 'center');
        $(this.el).dialog({ show: "slide" });
        $(this.el).dialog('open');
    },

    activeTab : function(event, ui) {
        this.tabCustomLoad(event, ui);
        $('.active',this.el).removeClass('active');
        $(event.target).parent('li').addClass('active');
        var tabDiv = $(event.target).attr('ref');
        $(tabDiv).addClass('active');
    },

    getActiveTabId: function(){
        return $('li.active a',this.el).attr('id');
    },

    tabSwitcher: function(event, ui){
        var tab = $(event.currentTarget).attr('ref');
        $(tab).show();
        $(tab).trigger('click');
    },

    /* Can be overwritten to perform custom actions on tab activation */
    tabCustomLoad: function(){},

    save : function() {
        var formData = toDict($('form', this.el).serializeArray());
        this.additionalSave(formData);
        if ( this.updateItems ) {
            var items = this.tableView.toJSON();
            this.model.setItems(items);
        }
    },

    additionalSave: function(formData) {
        this.model.set(formData);
    },

    getTabHtml: function(tab) {
        var self = this;
        var name = tab.type + '-' + self.model.get('id');
        if ( tab.type == 'addSession' ) {
            var disabledSessions = [];
            _.each(self.sessionsModel.get('sessions'), function (el) {
                if ( ! self.model.hasSession(el.id) ){
                    disabledSessions.push(el);
                }
            });
            ret = self.getSectionEdit(name, { sessions : disabledSessions } );
        } else {
            ret = self.getSectionEdit(name, self.model.toJSON());
        }
        return ret;
    },

    getSectionEdit: function( tplId, dict ) {
        var tpl = TemplateManager.getSync('RegistrationForm','regFormSectionEditDialog',tplId);
        if (tpl === null ){
            tpl = $T("Error : Template not found!");
        }
        dict.getTabHtml = _.bind(this.getTabHtml, this);
        return nunenv.render("regFormSectionEditDialog.tpl", dict);
    },

    // Avoid form to but submitted when user presses enter
    submitForm: function(event) {
        event.preventDefault();
    }
});


var RegFormSessionsDialogView = RegFormSectionBaseDialogView.extend({

    initialize: function(model){
        this.constructor.__super__.initialize.apply(this, [model]);
        this.sessionsModel = new ConferenceSessions();
    },

    tabCustomLoad : function(event, ui){
        if( $(event.target).attr('id') == 'tab-editSessions' ) {
            this.sessionsTable();
        }
    },

    additionalSave: function(formData) {
        this.model.setConfig(formData);
    },

    sessionsTable : function(event, ui){
        var self = this;
        self.updateItems = true;
        if (typeof this.tableView === 'undefined') {
            // add disabled sessions to the model
            _.each(self.sessionsModel.get('sessions'), function (el) {
                if ( ! self.model.hasSession(el.id) ){
                    self.model.get('items').push({ id : '' + el.id, caption : el.caption, billable : false, price : 0, enabled : false } );
                }
            });
            this.tableView = new EditionTable (this.model, $('#editionTable', this.el) );
        }
    }
});


var RegFormAccommodationDialogView = RegFormSectionBaseDialogView.extend({

    events: _.extend({
            'click #addButton'  : 'addAccommodation'
        }, RegFormSectionBaseDialogView.prototype.events),

    additionalSave: function(formData) {
        this.model.setDatesOffsets(formData);
    },

    tabCustomLoad: function(event, ui){
        if (  $(event.target).attr('id') == 'tab-editAccomodation' ){
            this.accommodationTable();
        }
    },

    accommodationTable: function(event, ui){
        var self = this;
        self.updateItems = true;
        if (typeof this.tableView === 'undefined') {
            this.tableView = new EditionTable (this.model, $('#editionTable', this.el) );
        }
    },

    addAccommodation: function (event, ui) {
        event.stopPropagation();
        event.preventDefault();

        var newRowData = {
                id              : 'isNew',
                caption         : '',
                billable        : false,
                price           : '0',
                placesLimit     : '0'
        };
        this.tableView.addRow(newRowData);
    }
});


var RegFormSocialEventsDialogView = RegFormSectionBaseDialogView.extend({

    initialize: function(model){
        this.constructor.__super__.initialize.apply(this, [model]);
        this.tableConfigView = new EditionTable(this.model, $('#editionConfigTable', this.el));
        this.tableCancelView = new EditionTable(this.model, $('#editionCanceledTable', this.el), this.model.editTableCanceled);
        this.model.on('change',this.tableConfigView.render, this.tableConfigView);
        this.model.on('change',this.tableCancelView.render, this.tableCancelView);
    },

    events: _.extend({
            'click #addButton'          : 'addSocialEvent',
            'click #cancelEvent'        : 'cancelEvent',
            'click #undoCancelEvent'    : 'undoCancelEvent'
        }, RegFormSectionBaseDialogView.prototype.events),

    tabCustomLoad: function(event, ui){
        if(this.getActiveTabId() == 'tab-editEvents'){
            this.model.setItems(this.tableConfigView.toJSON());
        } else if (this.getActiveTabId() == 'tab-canceledEvent'){
            this.model.setItems(this.tableCancelView.toJSON());
        }
    },

    additionalSave: function(formData) {
        var itemsConfig = this.tableConfigView.toJSON();
        var itemsCancelled = this.tableCancelView.toJSON();
        this.model.set(formData);
        this.model.setItems(itemsConfig);
        this.model.setItems(itemsCancelled);
    },

    socialEventsTable: function(event, ui){
        var self = this;
        self.updateItems = true;
        if (typeof this.tableView === 'undefined') {
            this.tableView = new EditionTable(this.model, $('#editionTable', this.el) );
        }
    },

    tabSwitcher: function(event, ui){
        var socialEventId = $(event.currentTarget).closest('tr').attr('id');
        var cancelled = 'false';
        if(this.getActiveTabId() == 'tab-editEvents'){
            cancelled = 'true';
        }
        this.model.setItems([{
            id          : socialEventId,
            cancelled   : cancelled
        }]);
        var tab = $(event.currentTarget).attr('ref');
        var tabDiv = $(tab).attr('ref');
        $(tab).trigger('click');
    },

    cancelEvent: function (event,ui){
        this.socialEvent.reason = $('#cancelledReason').val();
        this.socialEvent.cancelled = true;
        this.model.setItems([this.socialEvent]);
    },

    undoCancelEvent: function(event,ui){

    },

    addSocialEvent: function (event, ui ){
        event.stopPropagation();
        event.preventDefault();

        var newRowData = {
                id                      : 'isNew',
                caption                 : '',
                billable                : false,
                price                   : '0',
                isPricePerPlace         : false,
                placesLimit             : '0',
                maxPlacePerRegistrant   : '8'
        };
        this.tableConfigView.addRow(newRowData);
    }
});
