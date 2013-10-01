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


var RegFormSectionsCreateView = Backbone.View.extend({

    events : {
        'click #buttonCreate'  : 'createSection',
        'submit form'          :  'submitForm'
    },

    initialize: function(){
        var self = this;
        $(this.el).dialog({
            modal: true,
            autoOpen: false,
            resizable: false,
            width : 'auto',
            title : $T('Create a new section'),
            autoResize:true,
            buttons: {
                    Create: function(){
                        self.createSection();
                        self.onClose();
                        self.clearInput();
                        $(this).dialog('close');
                    },
                    Close: function() {
                         self.onClose();
                         self.clearInput();
                         $(this).dialog('close');
                    }
            }

        });
        this.render();
    },

    render: function(){
        var self = this;
        $(self.el).empty();
        $(self.el).append(self.getTpl('infos'));
        $(self.el).append(self.getTpl('section-create'));
        return self;
    },

    clearInput: function(){
        $('form#newSectionForm', this.el).find('input:text, textarea').val('');
    },

    onClose: function(){ },

    show: function() {
        $('.regFormInfoMessage',self.el);
        $(this.el).dialog('open');
    },

    getTpl: function(tplId, dict) {
        var tpl = TemplateManager.getSync('RegistrationForm', 'regFormSectionsMgmt', tplId);
        return nunenv.render("regFormSectionsMgmt.tpl", dict);
    },

    createSection : function(){
        var sectionHeader = toDict($('form#newSectionForm',this.el).serializeArray());
        this.model.createSection({ sectionHeader : sectionHeader });
    },

    submitForm: function(event) {
        console.log(event);
        event.preventDefault();
    }

});
