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


/**
 * Renders the different fields for the registration form
 * @param {el} An el element must be passed. It indicates where
 *  the form must be inserted.
 */
var RegFormEditionView = RegFormDisplayView.extend({

    config: {
        sectionIdPrefix: 'section-',
        sortableFormClass: 'sortableForm',
        editableTextClass: 'editableText',
        editableItemClass: 'editableItem'
    },

    additionalEvents: {
        'click #buttonEditSection': '_editSectionDialog',
        'click #buttonCollpaseSection': '_collapseSection',
        'click #buttonDisableSection': '_disableSection',
        'click #buttonFieldEdit': '_editField',
        'click #buttonFieldRemove': '_setFieldStatus',
        'click #buttonFieldDisable': '_setFieldStatus',
        'click #buttonFieldEnable': '_setFieldStatus',
        'mouseenter .editableItem': '_displayFieldOptions',
        'mouseleave .editableItem': '_displayFieldOptions',
        'mouseenter .regFormFieldDisabled': '_displayDisabledFieldOptions',
        'mouseleave .regFormFieldDisabled': '_displayDisabledFieldOptions',
        'click .editableText': '_editSectionHeader'
    },

    initialize: function(el){
        var self = this;
        _.bindAll(this);

        // Load cache
        var templates = ['regFormEdit', 'regFormAddField', 'regFormSection', 'regFormFields',
                         'regFormFieldEdit', 'regFormSectionEditDialog', 'regFormSectionsMgmt'];
        var defer = TemplateManager.loadCache('RegistrationForm', templates);
        // Only listen on events from the model once the template needed for the rendering are loaded.
        defer.then( function() {
            self.model.on('change', self.render, self);
            self.model.fetch();
            self._dragAndDropForm();
        });

        self.editing = false;
        self.rfFields = new RegFormFieldsView(self);
        self.em = new ElementManager();
        self.classes = regForm.classes;
        self.model = new RegFormEdition();
        self.fieldEdition = new RegFormFieldsEditView({el : $('#edit-popup')}, self.model);
    },

    _setTooltips: function() {
        var self = this;
        $(this.el).find('.buttonAddField').qtip({
            content: {
                title: {
                    text: $T('Click on the new field to create'),
                    button : 'close'
                },
                text:  self.getTplAddField( self.model.getSectionById('0').get('fieldTypes'))
            },
            position: { my: 'top right', at: 'bottom left' },

            show: {  event: 'click', solo: true },

            hide: {
                event: 'unfocus click',
                fixed: true,
                effect: function() {
                    $(this).fadeOut(300);
                }
            },
            style: {
                classes: 'regFormAddField ui-tooltip-addField',
                width: '296px',
                padding: '20px',
                name: 'light'
            },

            events: {
                render: function(event, api) {
                    var that = this;
                    var sectionId = self._getSectionId($(api.elements.target));
                    $('.regFormAddFieldEntry', this).bind('click', function(event,ui) {
                        var newFieldType = $(event.target).closest('.regFormAddFieldEntry').data('fieldType').split('-');
                        var field = {
                            input   : newFieldType[0],
                            caption : '',
                            values  : {}
                        };
                        if(newFieldType[1]){
                            field.values.inputType = newFieldType[1];
                        }
                        self._createField(sectionId, field);
                        $(that).qtip('destroy');
                    });
                }
            }
        });
    },

    render: function(){
        var self = this;

        $(self.el).empty();
        _.each(self.model.get('sections'), function(section){
            var newSection = self.getSection({ section : section.toJSON() });
            var newSectionId = $(newSection).attr('id');
            $(self.el).append(newSection);
            $('#' + newSectionId).data('id', section.id);

            var elList = section.getHighlights();
            self._animateField(elList, newSectionId);
            section.emptyHighlights();

        });
        self._setCurrency();
        self._makeEditable();
        self._iconifySectionButtons();

        var elList = self.model.getHighlights();
        self._animateSection(elList);
        self.model.emptyHighlights();
        self._setTooltips();

        return self;
    },

    reload: function(){
        this.model.fetch();
    },

    getModel: function(){
        return this.model;
    },

    _animateSection: function(elList){
        var self = this;
        _.each(elList, function(el){
            var select = $("#" + self.config.sectionIdPrefix + el.id);
            $(select).effect("highlight", {}, 6000);
            $('html, body').animate({
              scrollTop: $(select).offset().top-200
            }, 1000);
        });
    },

    _animateField: function(elList, id){
        var self = this;
        _.each(elList, function(el){
            var select =  $("#" + id).find("#" + el.id);
            // Let some time to the browser to refresh the dom
            if(typeof select == 'undefined'){
                sleep(80);
                select =  $("#" + id).find("#" + el.id);
            }
            $(select).effect("highlight", {}, 6000);
        });
    },

    _getSectionId: function($element) {
        /*
          Returns the form section the $element in question is contained in
         */
        return $element.closest('.' + regForm.classes.section).data('sectionId');
    },

    _editSectionDialog: function(event, ui){
        if (this.editSectionDialogView) {
            this.editSectionDialogView.remove();
        }
        var sectionId = this._getSectionId($(event.target));
        var section = this.model.getSectionById(sectionId);
        this.editSectionDialogView = this._editSectionDialogMapper(section.get("_type"), section);
    },

    _editSectionDialogMapper: function (id, params){
        var maping = {
                'SessionsForm'          : RegFormSessionsDialogView,
                'SocialEventForm'       : RegFormSocialEventsDialogView,
                'AccommodationForm'     : RegFormAccommodationDialogView
        };
        return new maping[id](params);
    },

    //Make the form editable (drag&drop, remove, field edition, section edition)
    _makeEditable: function(section){
        var self = this;

        // add metadata
        $('.'+this.classes.title).data({itemType : 'title'});
        $('.'+this.classes.description).data({itemType : 'description'});
        $('.'+this.classes.text).data({itemType : 'description'});

        // To restrict the scope of the $ selection
        var selection = '';
        if (typeof section != 'undefined'){
            selected = $('#' + this.config.sectionIdPrefix + section.id);
        } else {
            selected = $(this.el);
        }

        // Make the fields draggable and droppable
        $('.' + this.classes.contentIsDragAndDrop).sortable( {
            cursor: 'move',
            opacity: 0.8
        });
        $('.' + this.config.sortableFormClass).sortable( {
            cursor: 'move',
            opacity: 0.8
        });

        // Make elements editable
        $('.'+this.classes.title, selected).addClass(this.config.editableTextClass);
        $('.'+this.classes.description, selected).addClass(this.config.editableTextClass);
        $('.'+this.classes.text, selected).addClass(this.config.editableTextClass);
        $('.'+this.classes.field, selected).addClass(this.config.editableItemClass);

        // Add section options (add, remove, disable) according to the locks
        $('.'+this.classes.header, selected).each( function (ind, el) {
            id = $(el).closest('.' + regForm.classes.section).data('sectionId');
            var actions = self.model.getSectionById(id).actions;
            $(el).before(self.getTplEditionItem('sectionButtons', { actions : actions }));
        });

        // Add default text for empty description of sections
        $.each($('.' + this.config.editableTextClass, selected),function(ind,val) {
            if($(val).text() === ''){
                $(val).text( $T("(click to add a description)") );
            }
        });
    },

    /* Button actions functions */
    _editField: function (event, ui){
        var sectionId = this._getSectionId($(event.target));
        var fieldId = $(event.currentTarget).closest('.' + this.config.editableItemClass).attr('id');
        this.fieldEdition.render(sectionId, fieldId);
    },

    _createField: function (sectionId, field){
        this.fieldEdition.render(sectionId, 'isNew', field);
    },

    _collapseSection: function (event) {
        if ($(event.currentTarget).closest('.'+this.classes.section).find('.'+this.classes.content).is(':visible')) {
            $(event.currentTarget).button( 'option', 'icons', {primary:'ui-icon-triangle-1-w'} );
        } else {
            $(event.currentTarget).button( 'option', 'icons', {primary:'ui-icon-triangle-1-s'} );
        }
        $(event.currentTarget).closest('.'+this.classes.section).find('.'+this.classes.content).slideToggle();
    },

    _disableSection: function (event){
        var self = this;
        new ConfirmPopup($T("Disable section"),
                         $T('Are you sure you want to disable this section? <br/>This action can be undone using "recover/discard sections" menu'),
                         function(action) {
                            if (action) {
                                var data = { 'sectionId' : self._getSectionId($(event.target)) };
                                self.model.disableSection(data);
                                var sectionEl = $(event.currentTarget).closest('.'+self.classes.section);
                                $(sectionEl).fadeOut('slow',function(){ $(sectionEl).remove(); });
                            }
                        }, $T("Disable")).open();
    },

    _performSetFieldStatus: function(field, data, silent) {
        this.model.getSectionById(data.sectionId).setFieldStatus(data, silent);
        $(field).fadeOut('slow',function(){ $(field).remove(); });

    },

    _setFieldStatus: function (event){
        var self = this;
        var actionsList = {
                'buttonFieldRemove'     : 'remove',
                'buttonFieldDisable'    : 'disable',
                'buttonFieldEnable'     : 'enable'
        };
        var field = $(event.currentTarget).closest('.' + this.config.editableItemClass + ', .' + regForm.classes.fieldDisabled);
        var data = {
            action: actionsList[$(event.currentTarget).attr('id')],
            sectionId: this._getSectionId($(event.target)),
            fieldId: $(field).attr('id')
        };

        if (data.action == 'remove') {
            new ConfirmPopup($T("Disable field"),
                             $T('Are you sure you want to disable this field? <br/>This action is irreversible.'),
                             function(action) {
                                if (action) {
                                    self._performSetFieldStatus(field, data, true);
                                }
                            }, $T("Disable")).open();
        } else {
            this._performSetFieldStatus(field, data, false);
        }
    },

    _editSectionHeader: function (event){
        if (this.editing === false ) {
            // Shared variables
            this.editing = true;
            this.currentTarget = event.target;

            // Data given to the template render
            var data = [];
            data.sectionId = this._getSectionId($(event.target));
            data.text = $(this.currentTarget).text();
            data.itemType = $(this.currentTarget).data().itemType;

            // Generate and insert the form
            var editionForm = this.getTplEditionItem('editionInputInlineForm',{data : data});
            $(this.currentTarget).before(this.em.addTmp(editionForm));

            // Apply the style the edited element on the form
            var styles = ['font-size', 'color', 'font-family', 'font-style', 'font-weight', 'float'];
            var i;
            for(i in styles) {
                $('.regFormInlineEdition').css(styles[i],$(this.currentTarget).css(styles[i]));
            }
            styles = ['padding', 'float', 'margin', 'clear'];
            for(i in styles){
                $('#changeEditionForm').css(styles[i],$(this.currentTarget).css(styles[i]));
            }
            this.em.addHidden(this.currentTarget);
            this._popupActionButtons();

        } else {
            alert($T('You are editing another Item'));
        }
    },

    _popupActionButtons: function(){
        var self = this;
        $('.regFormInlineEdition', this.el).qtip({
            content: {
                text:  '<input id="saveButton" class="qtipButton" type="submit" value="Save"></input>'+
                       '<input id="cancelButton" class="qtipButton" type="reset"  value="Cancel"></input>'
            },
            show: { event: false, ready: true },
            position: { my: 'top center', at: 'bottom center' },
            hide: false,
            style: {
                classes: 'ui-tooltip-shadow ui-tooltip-tipped',
                border: { width: 3, radius: 7}
            },
            events: {
                render: function(event, api) {
                    var that = this;

                    $('.qtipButton',this).bind('click', function(event) {
                        if(event.target.id == 'saveButton') {
                            data = $('#tmpEditionForm').serializeObject();
                            self.model.getSectionById(data.sectionId).updateHeader(data);
                        } else if (event.target.id == 'cancelButton'){

                        }
                        $(that).qtip('hide');
                        self.em.showHidden();
                        self.em.removeTmp();
                        self.editing = false;
                    });
                    $('#tmpEditionForm').bind('submit', function(event) {
                        event.preventDefault();
                        $("#saveButton",this.el).trigger('click');
                    });

                }
            }
        });
    },

    /* Hover actions */
    _displayFieldOptions: function (event, ui) {
        if(event.type == 'mouseenter' && this.editing === false){
            // Get locks
            var sectionId = this._getSectionId($(event.target));
            var fieldId = $(event.currentTarget).closest('.' + this.config.editableItemClass).attr('id');
            var field =  this.model.getSectionById(sectionId).getFieldById(fieldId);
            var dict = {locks: any(field.lock,[])};

            var editHTML = this.getTplEditionItem('fieldButtons', dict);
            var selector = $(event.currentTarget).closest('.' + this.config.editableItemClass).find('tr:first');
            $(selector).before('<tr><td colspan="2" align="right">'+$(editHTML).html()+'</td></tr>');
            this.em.addTmp($(event.currentTarget).closest('.' + this.config.editableItemClass).find('tr:first'));
            this._iconifyFieldButtons();
        }
        else if (this.editing === false) {
            this.em.removeTmp();
        }
    },

    _displayDisabledFieldOptions: function(event, ui) {
        if(event.type == 'mouseenter' && this.editing === false){
            var editHTML = this.getTplEditionItem('fieldDisabledButtons',{});
            var selector = $(event.currentTarget).closest('.' + regForm.classes.fieldDisabled).find('tr:first');
            $(selector).before('<tr><td colspan=2 align="right">'+$(editHTML).html()+'</td></tr>');
            this.em.addTmp($(event.currentTarget).closest('.' + regForm.classes.fieldDisabled).find('tr:first'));
            this._iconifyFieldButtons();
        }
        else if (this.editing === false) {
            this.em.removeTmp();
        }
    },

    /* animation and style functions */
    _iconifySectionButtons: function () {
        $( '.regFormButtonCollpase' ).button({
            icons: { primary: 'ui-icon-triangle-1-s' },
            text: false
        });
        $( '.regFormButtonTrash' ).button({
            icons: { primary: 'ui-icon-trash' },
            text: false
        });
        $( '.regFormButtonAdd' ).button({
            icons: { primary: 'ui-icon-plusthick' },
            text: false
        });
        $( '.regFormButtonEdition' ).button({
            icons: { primary: 'ui-icon-wrench' },
            text: false
        });
    },

    _iconifyFieldButtons: function (){
        $( '.regFormButtonEdition' ).button({
            icons: { primary: 'ui-icon-wrench' },
            text: false
        });
        $( '.regFormButtonDisable' ).button({
            icons: { primary: 'ui-icon-cancel' },
            text: false
        });
        $( '.regFormButtonRemove' ).button({
            icons: { primary: 'ui-icon-trash' },
            text: false
        });
        $( '.regFormButtonEnable' ).button({
            icons: { primary: 'ui-icon-check' },
            text: false
        });
    },

    /* Drag and drop functions */
    _dragAndDropForm: function() {
        var self = this;
        var sectionId;
        var fieldId;

        // Manage the drag and drop actions for the section and Items
        $('.' + this.config.sortableFormClass).bind('sortstop', function(event, ui) {
            event.stopPropagation();
            var data = {
                    'endPos'    :   ui.item.index(),
                    'sectionId' :   sectionId
            };
            // move a section
            if ($(ui.item).hasClass(regForm.classes.section)) {
                self.model.moveSection(data);
            }
            // move a field inside a section
            if ($(ui.item).hasClass(regForm.classes.field) || $(ui.item).hasClass(regForm.classes.fieldDisabled) ) {
                data.fieldId = fieldId;
                self.model.getSectionById(data.sectionId).moveField(data);
            }
        });
        // Save the initial position of the section/item
        $('.sortableForm').bind('sortstart', function(event, ui) {
            event.stopPropagation();
            sectionId = self._getSectionId($(ui.item));
            fieldId = $(ui.item).closest('.' + self.config.editableItemClass + ', .' + regForm.classes.fieldDisabled).attr('id');
        });
    },

    getTplEditionItem: function(tplId, dict) {
        var tpl = "edition/" + tplId + ".tpl";
        return nunenv.render(tpl, dict);
    },

    getTplAddField: function(dict) {
        return nunenv.render("regFormAddField.tpl", {fields: dict} );
    }
});


