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


/******************************************************
* Holds the all structure of the display of the form
*******************************************************/
var RegFormDisplay = RegFormBaseModel.extend({

    fetchMethod: 'regForm.registrationForm.FormDisplay',

    defaults: {
        currency: '',
        sections: []
    },

    setResult: function(result){
        this._setSections(result.sections);
        this.set('currency',result.currency);
    },

    getSectionById: function(id){
        return _.find(this.get('sections'), function(section){ return section.id == id || section.get('elId') == id; });
    },

    getSectionByType: function(type){
        return _.find(this.get('sections'), function(section){ return section.get('_type') == type; });
    },

    getAllDateInputs: function(){
        var dateInputs = [];
        _.each( this.get('sections'), function(section){
            if(section.get('_type') == "GeneralSectionForm" || section.get('_type') == "PersonalDataForm" ){
                dateInputs = concat(dateInputs,_.filter(section.get('items'), function(item){ return  item.values._type == "DateInput"; }));
            }
        });
        return dateInputs;
    },

    getFieldByHTMLName: function(HTMLName, sectionId){
        return _.find(this.getSectionById(sectionId).toJSON().items,
                function(item){ return  item.values.HTMLName == HTMLName; });
    },

    getItemIdByCaption: function(caption, fieldId, sectionId){
        var field = _.find(this.getSectionById(sectionId).getFieldById(fieldId).values.radioitems,
                function(item){ return  item.caption == caption; });
        return field.id;
    },

    linkSectionToElId: function(sectionId, elId){
        this.getSectionById(sectionId).set({ 'elId': elId }, {silent : true});
    },

    toJSON: function(){
        return $.parseJSON((JSON.stringify(this.get('sections'))));
    },

    _addSection: function(section) {
        section.on('change',this.change,this);
        this.get('sections').push(section);
    },

    _createSection: function (sectionJson){
        // remove disabled items
        sectionJson.items = _.filter(sectionJson.items, function(item) { return ! item.disabled === true; });
        var newSection = new RegFormSectionDisplayModel(sectionJson);
        this._addSection(newSection);
    },

    _setSections: function(newSections, silent){
        var self = this;
        self.set('sections',[], {silent:true});
        _.each(newSections, function(section){
            if (section.enabled) {
                self._createSection(section);
            }
        });
        if (!silent){
            this.trigger('change');
        }
    }
});

/********************************************************************************************
 * Section model for the display
 */

var RegFormSectionDisplayModel = Backbone.Model.extend({

    getFieldById: function(id){
        return _.find(this.get('items'), function(item){ return item.id == id;});
    }
});

/********************************************************************************************
 * User data model
 */
var RegFormUserDataModel = RegFormBaseModel.extend({

    fetchMethod: 'regForm.registrationForm.UserData',

    defaults: {
        accommodation: {},
        miscellaneousGroupList: [],
        reasonParticipation: "",
        sessionList: [],
        socialEvents: []
    },

    initialize: function () {
        this.fetch();
    }
});