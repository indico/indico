/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
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

type("DateTimeSelector", ["RealtimeTextBox", "ErrorAware"],
     {
         /*
          * direct: conversion should be bypassed (real value)
          * function returns server-compliant datetime string, null in case of empty input
          * or undefined in case of parsing error
          */
         get: function(direct) {

             var value = RealtimeTextBox.prototype.get.call(this);

             if (value && !direct) {
                 // convert formats, server <-> client
                 var dateTime = Util.parseDateTime(value, this.displayFormat);

                 if (dateTime) {
                     return Util.formatDateTime(dateTime, this.dateOnly ?
                             IndicoDateTimeFormats.ServerHourless : IndicoDateTimeFormats.Server);
                 } else {
                     return undefined;
                 }
             } else if (direct) {
                 return value;
             } else {
                 return null;
             }
         },

         draw: function() {
             this.enableEvent();
             return this.IWidget.prototype.draw.call(this, this.tab);
         },

         set: function(value, direct) {
             // let the programmer choose if for some reason
             // conversion should be bypassed
             if (!direct) {
                 // convert formats, server <-> client
                 var dateTime = Util.parseDateTime(value, this.dateOnly ?
                         IndicoDateTimeFormats.ServerHourless : IndicoDateTimeFormats.Server);
                 RealtimeTextBox.prototype.set.call(
                     this,
                     Util.formatDateTime(dateTime, this.displayFormat));
             } else {
                 RealtimeTextBox.prototype.set.call(this, value);
             }
         },

         _setErrorState: function(text) {

             var self = this;

             this._stopErrorList = this._setElementErrorState(this.input, text);

             if (text !== null) {
                 if (this.tab.dom.className.slice(-7) != "invalid") {
                     this.tab.dom.className += " invalid";
                 }
             }

             this._stopErrorList.push(function() {
                 if (self.tab.dom.className.slice(-7) == "invalid") {
                     self.tab.dom.className = self.tab.dom.className.substring(
                         0, self.tab.dom.className.length-8);
                 }
             });
         },

         _setElementErrorState: function(element, text) {
             // use "passive" mode, so that fields can be verified live
             return IndicoUtil.markInvalidField(element, text, true);
         },

         _checkErrorState: function() {

             var value = this.get(true);
             var validDate = value !== "" ? !!Util.parseJSDateTime(value, this.displayFormat) : null;

             if (validDate) {
                 return null;
             } else if (validDate == false){
                 return $T('Date is invalid');
             } else {
                 return this.mandatory ? $T('No date specified') : null;
             }
         }
     },
     function(args, format, mandatory, dateOnly) {
         this.dateOnly = dateOnly || false;
         this.displayFormat = format || (this.dateOnly ? IndicoDateTimeFormats.DefaultHourless : IndicoDateTimeFormats.Default);
         this.mandatory = mandatory || false;

         this.RealtimeTextBox(args);

         this.trigger = Html.img({src: imageSrc("calendarWidget")});
         this.tab = Html.div("dateField", this.input, this.trigger);
         var self = this;

         this.observe(function() {
             self.askForErrorCheck();
             return true;
         });

         var onSelect = function(cal) {
             var p = cal.params;
             var update = (cal.dateClicked || exists(cal.activeDiv._range)); // if there is _range we are updating the time
             if (update && p.inputField) {
                 p.inputField.value = cal.date.print(p.ifFormat);
                 if (typeof p.inputField.onchange == "function")
                     p.inputField.onchange();
             }
             if (update && p.displayArea)
                 p.displayArea.innerHTML = cal.date.print(p.daFormat);
             if (update && typeof p.onUpdate == "function")
                 p.onUpdate(cal);
         };

         // set up the calendar widget to appear on click
         Calendar.setup({
             inputField: this.input.dom,
             button: this.trigger.dom,
             displayArea: this.input,
             eventName: "click",
             ifFormat: this.displayFormat,
             showsTime: !dateOnly,
             align: "",
             // notify the selector each time a new date/time is set
             // (since onkeydown/onkeyup won't be called)
             onUpdate: function() { self.notifyChange(); },
             onSelect: onSelect
         });

     });


type("DateWidget", ["InlineEditWidget"],
        {
            __verifyDate: function() {
                this.date.askForErrorCheck();
                this._setSave(!this.date.inError());
            },
            _handleEditMode: function(value) {

                // create datefield
                this.date = new DateTimeSelector();

                // set them to the values that are passed
                this.date.set(Util.formatDateTime(value, IndicoDateTimeFormats.Server, IndicoDateTimeFormats.Default));

                var self = this;

                this.date.observe(function() {
                    self.__verifyDate();
                    return true;
                });

                return Html.span({}, this.date.draw());
            },

            _handleDisplayMode: function(value) {
                if(value){
                    return Util.formatDateTime(value, IndicoDateTimeFormats.Default, IndicoDateTimeFormats.Default);
                }
                else{
                    return $T("Date has not been set yet.")
                }
            },

            _getNewValue: function() {

                return Util.formatDateTime(this.date.get(), IndicoDateTimeFormats.Default, IndicoDateTimeFormats.Server);
            },

            _verifyInput: function() {
                return !!Util.parseDateTime(this.date.get());

            }
        },
        function(method, attributes, initValue) {
            this.InlineEditWidget(method, attributes, initValue);
        });


type("DateDeadlineWidget", ["DateWidget"],
        {
            _getNewValue: function() {
                return { date: Util.formatDateTime(this.date.get(), IndicoDateTimeFormats.Server, IndicoDateTimeFormats.Server),
                    applyToContributions: this.applyToContributions};
            },

            _handleSave: function() {
                var self = this;
                if(this.hasContributions){
                    new SpecialRemovePopup($T("Changing deadline"), $T("Do you want to apply this deadline to all the papers and replace their previous deadlines?"),
                            function(action) {
                                if (action > 0) {
                                    self.applyToContributions = action != 1;
                                    self._save();
                                }
                           }, $T("Save deadline only"), $T("Save and apply")).open();
                } else {
                    self.applyToContributions = false;
                    self._save();
                }
            }
        },
        function(method, attributes, initValue, hasContributions) {
            this.applyToContributions = false;
            this.hasContributions = hasContributions;
            this.DateWidget(method, attributes, initValue);
        });
