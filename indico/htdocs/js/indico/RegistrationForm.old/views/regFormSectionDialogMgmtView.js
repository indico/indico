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


var RegFormSectionsMgmtView = Backbone.View.extend({

    events : {
        'click #buttonRestore' : 'restoreSection',
        'click #buttonRemove'  : 'removeSection',
        'click #buttonCreate'  : 'createSection'
    },

    onClose: function(){ },

    initialize: function(){
        var self = this;
        self.model.on('reset', this.render, this);
        self.model.on('change', this.render, this);
        $(this.el).dialog({
            modal: true,
            autoOpen: false,
            resizable: false,
            width: 'auto',
            title : $T("Add, Remove or Restore a section"),
            autoResize:true,
            buttons: {
                    Close : function() {
                            self.model.trigger('change');
                            $(this).dialog('close');
                    }
            }
        });
    },

    render: function(){
        var self = this;
        $(self.el).empty();
        $(self.el).append(self.getTpl('infos',{}));
        _.each(this.model.getRawData().sections, function(section){
            if (section.enabled === false){
                $(self.el).append(self.getTpl('section',{ section : section }));
            }
        });
        $('.regFormButton', this.el).button();
        return self;

    },

    show : function() {
        this.model.fetch();
        $('.regFormInfoMessage',self.el);
        $(this.el).dialog('open');
    },

    getTpl: function( tplId, dict ) {
        var tpl = TemplateManager.getSync('RegistrationForm', 'regFormSectionsMgmt', tplId);
        return nunenv.render("regFormSectionsMgmt.tpl", dict);
    },

    restoreSection : function(event, ui){
        var self = this;
        var sectionDiv = $(event.target).closest('.regFormSectionMgmt');
        var data = { sectionId : $(sectionDiv).attr('id') };
        $(sectionDiv).fadeOut('slow', function() {
            var section = self.model.getRawSectionById($(sectionDiv).attr('id'));
            self.displayMessage($T("The section '{0}' has been restored to the registration form").format(section.title));
        });
        this.model.enableSection(data, true);
    },

    removeSection : function(event,ui){
        var self = this;
        var sectionDiv = $(event.target).closest('.regFormSectionMgmt');
        var data = { sectionId : $(sectionDiv).attr('id') };

        new ConfirmPopup($T("Remove section"),
                 $T('Are you sure you want to remove this section? <br/>This action is irreversible.'),
                 function(action) {
                    if (action) {
                        $(sectionDiv).fadeOut('slow', function() {
                            var section = self.model.getRawSectionById($(sectionDiv).attr('id'));
                            self.displayMessage($T("The section '{0}' has been removed from the registration form").format(section.title));
                        });
                        self.model.removeSection(data, true);
                    }
                }, $T("Remove")).open();
    },

    createSection : function(event,ui){
        this.displayMessage($T("A geneal section has been added to the registration form"));
        this.model.createSection({});
    },

    displayMessage : function(message) {
        var self = this;
        var messageDiv = $('.regFormInfoMessage',self.el);
        if($(messageDiv).is(':hidden') === true){
            $(messageDiv).show();
            $(messageDiv).html(self.getTpl('message',{message : message}));
            $(messageDiv).children().hide();
            $(messageDiv).children().fadeIn('slow');
        } else {
            $(messageDiv).children().fadeOut('slow', function() {
                $(messageDiv).html(self.getTpl('message',{message : message}));
                $(messageDiv).children().hide();
                $(messageDiv).children().fadeIn('slow');
            });
        }
    }
});
