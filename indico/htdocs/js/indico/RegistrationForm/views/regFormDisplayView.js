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
 * @param {regFormUtilsDisplay}
 */
var RegFormFieldsView = Backbone.View.extend({

    initialize: function (){
        _.bindAll(this);
    },

    render: function(field, sectionId){
        // Check if the input type is supported
        var allowedType = ['text','radio', 'country', 'date', 'file', 'textarea', 'checkbox', 'radiogroup', 'label', 'number', 'telephone', 'yes/no', 'yesno'];
        if(allowedType.indexOf(field.input) < 0 ){
            console.log('Type : ' + field.input + ' is not supported yet');
            field.input='text';
        }

        var fieldHtml = '';
        switch (field.input){
            case 'checkbox':
                fieldHtml = this._getWrapper(field,sectionId,'itemWrapAllRight');
                break;
            case 'label':
                fieldHtml = this._getTplField('label', { classes : regForm.classes, field : field });
                break;
            case 'yes/no':
                field.input = 'yesno';
                fieldHtml =  this._getWrapper(field, sectionId);
                break;
            default:
                fieldHtml = this._getWrapper(field, sectionId);
        }
        return fieldHtml;
    },

    _getWrapper: function(field, sectionId, wrapperId) {
        wrapperId = any(wrapperId, 'itemWrapStd');
        var name = this._getFieldName(field, sectionId);
        var item = this._getTplField( field.input,
                {
                    field       : field,
                    classes     : regForm.classes,
                    name        : name
                });
        wrapper = this._getTplField(wrapperId,
                {
                    field       : field,
                    classes     : regForm.classes,
                    item        : item
                });
        return wrapper;
    },

    _getFieldName: function(field, sectionId){
        var name;
        if (field.input == 'date'){
            name = '_genfield_'+sectionId+'_'+field.id;
        } else {
            name = '*genfield*'+sectionId+'-'+field.id;
        }
        return name;
    },

    _getTplField: function(tplId, dict) {
        var attributes = "";
        if( dict.field.mandatory === true) {
            attributes = "required";
        }
        if ( dict.field.placesLimit !== 0 &&  dict.field.noPlacesLeft === 0){
            attributes = attributes + " disabled";
        }
        dict.attributes = attributes;
        var tpl = TemplateManager.getSync('RegistrationForm','regFormFields',tplId);
        return nunenv.render("regFormFields.tpl", dict);
    }
});

/**
 * Renders the different fields for the registration form
 * @param {el} An el element must be passed. It indicates where
 *  the form must be inserted.
 */
var RegFormDisplayView = Backbone.View.extend({

    originalEvents: {},

    additionalEvents: {},

    events: function() {
        return _.extend({},this.originalEvents,this.additionalEvents);
    },

    initialize: function(el){
        var self = this;
        self.dateInputHandlers = {};
        self.classes = regForm.classes;
        self.model = new RegFormDisplay();

        var templates = ['regFormSections', 'regFormFields'];
        var defer = TemplateManager.loadCache('RegistrationForm', templates);
        defer.then( function() {
            self.rfFields = new RegFormFieldsView(self);
            self.model.on('reset', self.render, self);
            self.model.on('change', self.render, self);
            self.model.fetch();

            self.userDataModel = new RegFormUserDataModel();
            self.userDataModel.on('reset', self.insertData, self);
            self.userDataModel.on('change', self.insertData, self);
        });
    },

    render: function(){
        var self = this;
        self.dateInputHandlers = {};
        $(self.el).empty();
        _.each(self.model.get('sections'), function(section){
            var newSection = self.getSection({ section : section.toJSON() });
            $(self.el).append(newSection);
        });
        this._setCurrency();
        this.insertData();
        this.enableEmpytDateInput();
        return self;
    },

    getSection: function( dict ) {
        var self = this;
        dict.classes = self.classes;
        dict.fields = self.rfFields;
        var tpl = TemplateManager.getCached('RegistrationForm','regFormSections', false);
        return nunenv.render("regFormSections.tpl", dict);
    },

    insertData: function(){
        var self = this;
        var data = this.userDataModel.toJSON();

        // insert avatar user information
        _.each(data.avatar, function(value, name){
            var sectionStuct = self.model.getSectionByType('PersonalDataForm');
            var section = self.getSectionElById(sectionStuct.get('id'));
            $(section).find("[name = '" + name + "']").val(value);
        });

        // insert data in all general form
        _.each(data.miscellaneousGroupList, function(sectionUD){
           var section = self.getSectionElById(sectionUD.id);
           _.each(sectionUD.responseItems, function(item){
               var field = $(section).find("[name= '" + item.HTMLName + "']");
               // Get the type of the element
               var fieldType = $(field).attr('type');
               if(item.HTMLName.indexOf("_genfield_") != -1 ){
                   fieldType = "date";
               } else if ($(field).is('select')){
                   fieldType = "select";
               }

               // Set the value
               if(fieldType == 'checkbox'){
                   $(field).prop('checked',item.value == "yes");
               } else if(fieldType == 'radio'){
                   var id = self.model.getItemIdByCaption(item.value, item.id, $(section).data('id'));
                   var fieldSelected = _.find(field, function(el){ return $(el).attr('value') == id; });
                   $(fieldSelected).prop("checked", true);
               } else if(fieldType == 'date'){
                   self.setDateInput(item, section);
               } else if(fieldType == 'select'){
                   var selectEl =  $(section).find("[name = '" + item.HTMLName + "']");
                   $(selectEl).val(item.value);
                   // If value is the caption and not the id
                   if( ! _.isEmpty(item.value) && item.value !=  $(selectEl).val() ){
                       var id = self.model.getItemIdByCaption(item.value, item.id, $(section).data('id'));
                       $(selectEl).val(id);
                   }
               } else {
                   $(section).find("[name = '" + item.HTMLName + "']").val(item.value);
               }
               // If payed and that the item is billable set the save price and currency
               if (data.payed && $(section).find("[name = '" + item.HTMLName + "']").hasClass(regForm.classes.billable)){
                   // Set currency
                   self._setItemCurrency(item);
               }
           });
           // refresh number display with new value
           $("[type=number]", this.el).trigger('change');
        });

        // insert data in reason of participation form
        if (! _.isEmpty(data.reasonParticipation)){
            var section = self.getSectionElById('reasonParticipation');
            $(section).find("[name = reason]").val(data.reasonParticipation);
        }

        // insert data in session form
        _.each(data.sessionList, function(session, ind){
            var section = self.getSectionElById('sessions');
            if($(section).find("[name=sessions]").attr('type') == "checkbox"){
                $(section).find("[name=sessions][value = " + session.id + "]").prop('checked',true);
            } else {
                $(section).find("#session" + (ind + 1)).val(session.id);
            }

        });

        // insert data in accommodation form
        if (! _.isEmpty(data.accommodation)){
            var acc = data.accommodation;
            var section = self.getSectionElById('accommodation');
            $(section).find("[name = 'arrivalDate']").val(acc.arrivalDate);
            $(section).find("[name = 'departureDate']").val(acc.departureDate);
            $(section).find("#" + acc.accommodationType.id + "[name = accommodation_type]").prop('checked', true);
            // if payed update the price and the currency
            if(data.payed){
                var itemSelector = $(section).find("#" + acc.accommodationType.id + "[name = accommodation_type]").closest('tr');
                if(typeof acc.accommodationType.currency != 'undefined'){
                    $(itemSelector).find("." + regForm.classes.currency).html(acc.accommodationType.currency);
                }
                if(typeof acc.accommodationType.price != 'undefined' && acc.accommodationType.price !== ''){
                    $(itemSelector).find("." + regForm.classes.price).html(acc.accommodationType.price);
                }
            }
        }

        // insert data in social events form
        if (! _.isEmpty(data.socialEvents)){
            var section = self.getSectionElById('socialEvents');
            _.each(data.socialEvents, function(se){
                $(section).find("[name = 'socialEvents'][value =" + se.id + "]").prop("checked",true);
                $(section).find("[name = 'places-" + se.id + "']"). val(se.noPlaces);
                if(data.payed){
                    var itemSelector = $(section).find("[name = 'socialEvents'][value =" + se.id + "]").closest('tr');
                    if(typeof se.currency != 'undefined'){
                        $(itemSelector).find("." + regForm.classes.currency).html(se.currency);
                    }
                    if(typeof se.price != 'undefined' && se.price !== ''){
                        $(itemSelector).find("." + regForm.classes.price).html(se.price);
                    }
                }
            });
        }

        // If field has been disabled because no place were left but that the registrant
        // selected if before then enable this field.
        $('*:disabled', this.el).attr('disabled', false);

        if (data.payed){
            // Disable all billable element
            $("." + regForm.classes.billable, this.el).prop('disabled', true);
            $("." + regForm.classes.billable, this.el).attr('title', $T('No modification are allowed after payment'));

            // If the billable element is a radio button disable all related radio buttons
            _.each($(".regFormIsBillable:radio", this.el), function(el, ind){
                $('[name="' + el.name + '"]',this.el).prop('disabled',true);
            });

            // Disable accommodation form
            $("#section-accommodation").find('select, *:radio').prop('disabled', true);
            $("#section-accommodation").find('select, *:radio').attr('title', $T('No modification are allowed after payment'));

            // Disable social events if using radio buttons and that there is at least one billable element inside.
            if($("#section-socialEvents").find('*:radio.' + regForm.classes.isBillable)){
                $("#section-socialEvents").find('select, *:radio').prop('disabled', true);
                $("#section-socialEvents").find('select, *:radio').attr('title', $T('No modification are allowed after payment'));
            }


        }
    },


    getSectionElById: function(id){
        var section = "";
        _.each( $(this.el).children(".regFormSection"), function(el){
            if ($(el).data('id') == id) {
                section = el;
            }
        });
        return section;
    },

    setDateInput: function(DateInputData, section){
        var self = this;
        var name = DateInputData.HTMLName;

        // If date input is still in the form
        var DateInputStruct = this.model.getFieldByHTMLName(name,$(section).data('id'));
        if(typeof DateInputStruct != 'undefined'){
            var format = DateInputStruct.values.dateFormat;
            var isWithTime = false;
            var datesHandler = new DateTimeSelectorWFields({}, format, false, isWithTime,
                  [name + 'Day', name + 'Month', name + 'Year', name + 'Hour', name + 'Min']);
            $E(name + 'DatePlace').set(datesHandler.draw());
            datesHandler.plugParameterManager(parameterManager);
            if(DateInputData.value !== null){
                datesHandler.set(Util.formatDateTime(DateInputData.value.date + " " + DateInputData.value.time,format,"%Y-%m-%d %H:%M:%s"), true);
                var DateArray = DateInputData.value.date.split('-');
                var TimeArray = DateInputData.value.time.split(':');
                $(section).find("[name = '" + name + "Year']").val(DateArray[0]);
                $(section).find("[name = '" + name + "Month']").val(DateArray[1]);
                $(section).find("[name = '" + name + "Day']").val(DateArray[2]);
                $(section).find("[name = '" + name + "Hour']").val(TimeArray[0]);
                $(section).find("[name = '" + name + "Min']").val(TimeArray[1]);
            }

            self.dateInputHandlers[name] = datesHandler;
        } else {
            self.dateInputHandlers[name] = false;
        }
    },

    enableEmpytDateInput: function(){
        var self = this;
        _.each(this.model.getAllDateInputs(), function(dateInput){
            var name = dateInput.values.HTMLName;
            if(typeof  self.dateInputHandlers[name] == 'undefined'){
                var format = dateInput.values.dateFormat;
                var datesHandler = new DateTimeSelectorWFields({}, format, false, false,
                      [name + 'Day', name + 'Month', name + 'Year', name + 'Hour', name + 'Min']);
                $E(name + 'DatePlace').set(datesHandler.draw());
                datesHandler.plugParameterManager(parameterManager);
                self.dateInputHandlers[name] = datesHandler;
            }
        });
    },

    _setItemCurrency: function(item){
        var itemSelector = $(this.el).find("[name = '" + item.HTMLName + "']").closest('tr');
        if(typeof item.currency != 'undefined'){
            $(itemSelector).find("." + regForm.classes.currency).html(item.currency);
        }
        if(typeof item.price != 'undefined' && item.price !== ''){
            $(itemSelector).find("." + regForm.classes.price).html(item.price);
        }
    },

    _setCurrency: function(){
        $("." + this.classes.currency).html(this.model.get('currency'));
    }
});

