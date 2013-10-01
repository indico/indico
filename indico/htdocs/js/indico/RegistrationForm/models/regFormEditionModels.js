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
* Holds the all structure of the form
*******************************************************/
var RegFormEdition = RegFormDisplay.extend({

    fetchMethod: 'regForm.registrationForm.FormModification',

    setResult: function(result) {
        this.set('result', result, {silent : true});
        this._setSections(result.sections);
        this.set('currency', result.currency);
    },

    change: function() {
        this.trigger('change');
    },

    createSection: function (data) {
        this._commit("SectionCreate", data, false);
    },

    moveSection: function(data) {
        this._commit("SectionMove", data, true);
    },

    disableSection: function(data) {
        this._commit("SectionDisable", data, true);
    },

    enableSection : function(data, silent) {
        this._commit("SectionEnable", data, silent);
    },

    removeSection : function(data, silent) {
        this._commit('SectionRemove', data, silent);
    },

    getRawData: function() {
        return this.get('result');
    },

    getRawSectionById: function(id) {
        return _.find(this.get('result').sections, function(section){ return section.id == id; });
    },

    _createSection: function(sectionJson) {
        // check if section is not already in the form
        var section = this.getSectionById(sectionJson.id);
        if (typeof section == 'undefined') {
            // create and add new section to the form
            var newSection = this.sectionMapper(sectionJson._type, sectionJson);
            this._addSection(newSection);
        }
    },

    _commit: function(method, params, silent) {
        RegFormBaseModel.prototype._commit.call(this, method, params, _.bind(this._setSections, this), silent);
    },

    sectionMapper: function(id,param) {
        var mapper = {
            'GeneralSectionForm'        : GeneralSection,
            'PersonalDataForm'          : PersonalDataSection,
            'ReasonParticipationForm'   : ReasonParticipationSection,
            'SessionsForm'              : SessionsSection,
            'AccommodationForm'         : AccommodationSection,
            'FurtherInformationForm'    : FurtherInformationSection,
            'SocialEventForm'           : SocialEventSection
        };
        return new mapper[id](param);
    }
});



/************************************************************************
 * Base section
 * All common items
 ************************************************************************/

var SectionBase = RegFormBaseModel.extend({

    actions: [''],

    defaults: {
        _type: '',
        _fossil: '',
        title: '',
        description: '',
        required: false,
        enabled: true
    },

    updateHeader: function( data ) {
        this._commit('SectionSetHeader', data, true, false);
    },

    commitDefaultParams: function(params) {
        params.confId = getConfId();
        params.sectionId = this.get('id');
        return params;
    }
});

/**************************************************************************
* Section Types
****************************************************************************/
var GeneralSection = SectionBase.extend({

    actions: ['disable','addField'],

    defaults: _.extend({},SectionBase.prototype.defaults, {
        items: null,
        fieldTypes: [
            { id: 'label',            desc: $T("Label") },
            { id: 'text',             desc: $T("Text input") },
            { id: 'number',           desc: $T("Number") },
            { id: 'textarea',         desc: $T("Text area") },
            { id: 'radio-dropdown',   desc: $T("Dropdown") },
            { id: 'radio-radiogroup', desc: $T("Choice") },
            { id: 'checkbox',         desc: $T("Checkbox") },
            { id: 'date',             desc: $T("Date") },
            { id: 'yesno',            desc: $T("Yes/No") },
            { id: 'telephone',        desc: $T("Phone") },
            { id: 'country',          desc: $T("Country") },
            { id: 'file',             desc: $T("File") }
            ]
        }
    ),

    createField: function(data) {
        this._commit('FieldCreate', data, true, false);
    },

    setFieldStatus: function(data, silent) {
        silent = typeof silent !== 'undefined' ? silent: false;
        this._commit('FieldSetStatus', data, true, silent);
    },

    updateField: function(data) {
        this._commit('FieldSet', data, true, false);
    },

    moveField: function(data) {
        this._commit('FieldMove', data, true, false);
    },

    setFieldItems: function(data) {
        this._commit('FieldRadioSetItems', data, true, false);
    },

    getFieldById: function(id) {
        return _.find(this.get('items'), function(item) {
            return item.id == id;
        });
    }
});

var PersonalDataSection = GeneralSection.extend({
    actions: ['addField']
});

var ReasonParticipationSection = SectionBase.extend({
    actions: ['disable']
});

var SessionsSection = SectionBase.extend({

    actions: ['disable','settings'],

    defaults: _.extend({},SectionBase.prototype.defaults, {
        type:'2priorities',
        items: [],
        tabs :[ { id: 'config',         name: $T("Configuration"),        type    : 'config' },
                { id: 'editSessions',   name: $T("Manage sessions"),      type    : 'editionTable' }
               ]
        }
    ),

    hasSession: function(id) {
        var item = _.find(this.get('items'), function(item){ return item.id == id;});
        return typeof item != 'undefined';
    },

    setItems: function (items) {
        this._commit('SectionSessionsSetItems', {items: items }, true, false );
    },

    setConfig: function(data) {
        this._commit('SectionSessionsSetConfig', data, true, false);
    },

    editTableConfig: {
        data: 'items',
        sortable: false,
        width : 500,
        actions: [''],
        colNames:[$T('caption'),$T('billable'),$T('price'), $T('enabled')],
        colModel:[
                   {
                       name:'caption',
                       index:'caption',
                       align: 'left',
                       sortable:false,
                       width:200,
                       editoptions:{size:"30",maxlength:"80"},
                       editable: false
                   },
                   {
                       name:'billable',
                       index:'billable',
                       sortable:false,
                       width:60,
                       editable: true,
                       align: 'center',
                       edittype:'bool_select',
                       defaultVal: true
                   },
                   {
                       name:'price',
                       index:'price',
                       align: 'center',
                       sortable:false,
                       width:80,
                       editable: true,
                       editoptions:{size:"7",maxlength:"20"}

                   },
                   {
                       name:'enabled',
                       index:'enabled',
                       sortable:false,
                       width:60,
                       editable: true,
                       align: 'center',
                       edittype:'bool_select',
                       defaultVal: true
                   }
                 ]
    }
});

var AccommodationSection = SectionBase.extend({

        actions: ['disable','settings'],

        defaults: _.extend({}, SectionBase.prototype.defaults, {
            arrivalOffsetDates: [],
            departureOffsetDates: [],
            currency: 'CHF',
            items: [],
            tabs :[ { id: 'config',               name: $T("Configuration"),             type    : 'config' },
                    { id: 'editAccomodation',     name: $T("Edit accommodations"),       type    : 'editionTable' }
                   ]
            }
        ),

        setItems: function (items) {
            this._commit('SectionAccommodationSetItems', {items: items }, true, false );
        },

        setDatesOffsets: function(datesOffsets) {
            this._commit('SectionAccommodationSetConfig', { datesOffsets: datesOffsets  }, true, false );
        },

        editTableConfig: {
            data: 'items',
            sortable: false,
            width : 615,
            actions: ['remove'],
            colNames:[$T("caption"), $T("billable"),  $T("price"), $T("place limit"), $T("cancelled")],
            colModel: [
                      {
                           name:'caption',
                           index:'caption',
                           align: 'center',
                           sortable:false,
                           width:100,
                           editoptions: {size:"30",maxlength:"50"},
                           editable: true
                       },
                       {
                           name:'billable',
                           index:'billable',
                           sortable:false,
                           width:60,
                           editable: true,
                           align: 'center',
                           edittype:'bool_select',
                           defaultVal: true

                       },
                       {
                           name:'price',
                           index:'price',
                           align: 'center',
                           sortable:false,
                           width:50,
                           editable: true,
                           editoptions:{size:"7",maxlength:"20"}

                       },
                       {
                           name:'placesLimit',
                           index:'placesLimit',
                           align: 'center',
                           sortable:false,
                           width:80,
                           editable: true,
                           editoptions:{size:"7",maxlength:"20"}

                       },
                       {
                           name:'cancelled',
                           index:'cancelled',
                           sortable:false,
                           width:60,
                           editable: true,
                           align: 'center',
                           defaultVal: false,
                           edittype:'bool_select'
                       }

                  ]
        }
});

var FurtherInformationSection = SectionBase.extend({

    actions: ['disable'],

    defaults: _.extend({},SectionBase.prototype.defaults, {
            content: ''
        }
    )
});

var SocialEventSection = SectionBase.extend({

    actions: ['disable','settings'],

    defaults: _.extend({},SectionBase.prototype.defaults, {
            introSentence: '',
            selectionType: '',
            items: [],
            tabs :[ { id: 'config'              , name: $T("Configuration")     , type: 'config' },
                    { id: 'editEvents'          , name: $T("Edit events")       , type: 'editionTable' },
                    { id: 'canceledEvent'       , name: $T("Canceled events")   , type: 'cancelEvent' }
                   ]
        }
    ),

    setItems: function(items) {
        this._commit('SectionSocialEventsSetItems', {items: items }, true, false );
    },

    change: function(){
       if ( this.hasChanged('introSentence') || this.hasChanged('selectionType') ) {
           this._commit('SectionSocialEventsSetConfig', {
               intro: this.get('introSentence'),
               selectionType: this.get('selectionType')
            }, false );
      }
      this.trigger('change');
    },

    getSocialEventById: function(id) {
        return _.find(this.get('items'), function(item){ return item.id == id;});
    },

    getTabConfigById: function(divId) {
        var id = divId.split('-')[1];
        return _.find(this.get('tabs'), function(tab){ return tab.id == id;});
    },

    editTableConfig: {
        data: 'items',
        sortable: false,
        width : 750,
        actions: ['remove', [$T('Cancel this event'),'#tab-canceledEvent','ui-icon-cancel']],
        colNames:[$T("caption"), $T("billabe"), $T("price"), $T("price/place"), $T("Nb places"), $T("Max./part.")],
        displayCond: function(item){
            return item.cancelled === false;
        },
        colModel:[
                   {
                       name:'caption',
                       index:'caption',
                       align: 'center',
                       sortable:false,
                       width:160,
                       editoptions:{size:"30",maxlength:"50"},
                       editable: true
                   },
                   {
                       name:'billable',
                       index:'billable',
                       sortable:false,
                       width:60,
                       editable: true,
                       align: 'center',
                       defaultVal : false,
                       edittype:'bool_select'
                   },

                   {
                       name:'price',
                       index:'price',
                       align: 'center',
                       sortable:false,
                       width:50,
                       editable: true,
                       editoptions:{size:"7",maxlength:"20"}

                   },
                   {
                       name:'pricePerPlace',
                       index:'isPricePerPlace',
                       sortable:false,
                       width:80,
                       editable: true,
                       align: 'center',
                       defaultVal : false,
                       edittype:'bool_select'
                   },

                   {
                       name:'placesLimit',
                       index:'placesLimit',
                       align: 'center',
                       sortable:false,
                       width:80,
                       editable: true,
                       editoptions:{size:"7",maxlength:"20"}
                   },

                   {
                       name:'maxPlace',
                       index:'maxPlacePerRegistrant',
                       align: 'center',
                       sortable:false,
                       width:80,
                       editable: true,
                       editoptions:{size:"7",maxlength:"20"}

                   }
                 ]
    },

    editTableCanceled: {
        data: 'items',
        sortable: false,
        width : 800,
        actions: ['remove', [$T('Uncancel this event'),'#tab-editEvents','ui-icon-cancel']],
        colNames:[$T("caption"), $T("Reason for cancellation")],
        displayCond: function(item){
            return !item.cancelled === false;
        },
        colModel:[
                   {
                       index:'caption',
                       align: 'center',
                       sortable:false,
                       width:160,
                       editoptions:{size:"30",maxlength:"50"},
                       editable: false
                   },
                   {
                       name:'reason',
                       index:'cancelledReason',
                       sortable:false,
                       width:250,
                       editoptions:{size:"30",maxlength:"50"},
                       editable: true
                   }
                 ]
    }
});

var ConferenceSessions = RegFormBaseModel.extend({

    fetchMethod: 'event.sessions.listAll',

    defaults: {
        result:  {},
        sessions:  []
    },

    initialize: function() {
        this.fetch();
    },

    setResult: function(result) {
        this.set({result: result});
    },

    change: function () {
        if (this.hasChanged('result')) {
            var sessions = [];
            _.each(this.get('result'), function (el,ind) {
                // extract Id
                var id = ind.split('l')[0].split('s')[1];
                sessions.push({id: id, caption: el});
            });
            this.set('sessions', sessions, { silent: true });
        }
        this.trigger('change');
    }
});

/********************************************************************************************
 * Field item edition model
 *
 */
var RadioFieldModel = Backbone.Model.extend({

    defaults: {
        items: []
    },

    editTableConfig: {
        data: 'radioitems',
        sortable: false,
        width : 'auto',
        actions: ['remove', 'sortable'],
        colNames:[$T("caption"), $T("billable"), $T("price"), $T("places limit"), $T("enable")],
        colModel:[
                   {
                       name:'caption',
                       index:'caption',
                       align: 'center',
                       sortable:false,
                       width:160,
                       editoptions:{size:"30",maxlength:"50"},
                       editable: true
                   },
                   {
                       name:'billable',
                       index:'isBillable',
                       sortable:false,
                       width:60,
                       editable: true,
                       align: 'center',
                       defaultVal: false,
                       edittype:'bool_select'
                   },

                   {
                       name:'price',
                       index:'price',
                       align: 'center',
                       sortable:false,
                       width:50,
                       editable: true,
                       editoptions:{size:"7",maxlength:"20"}

                   },
                   {
                       name:'placesLimit',
                       index:'placesLimit',
                       align: 'center',
                       sortable:false,
                       width:80,
                       editable: true,
                       editoptions:{size:"7",maxlength:"20"}

                   },
                   {
                       name:'isEnabled',
                       index:'isEnabled',
                       sortable:false,
                       width:60,
                       editable: true,
                       align: 'center',
                       edittype:'bool_select',
                       defaultVal: true
                   }
                 ]
    }
});
