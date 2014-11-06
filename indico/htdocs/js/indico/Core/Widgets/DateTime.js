/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

type("DateSelector", ["DateTimeSelector"], { }, function(args, format, mandatory) {
    return this.DateTimeSelector(args, format, mandatory, true);
});

type("StartEndDateWidget", ["InlineEditWidget"],
     {
         /* builds the basic structure for both display and
            edit modes */
         __buildStructure: function(start, end) {
             // keep everything in separate lines
             return Html.table({},
                     Html.tbody({},
                             Html.tr("startEndDate",
                                     Html.td("startEndDateEntry", "Starts :"),
                                     Html.td({}, start)),
                             Html.tr("startEndDate",
                                     Html.td("startEndDateEntry", "Ends :"),
                                     Html.td({}, end))));
         },

         __verifyDates: function() {

             var valid = true;

             this.startDate.askForErrorCheck();
             this.endDate.askForErrorCheck();
             if (this.startDate.inError() || this.endDate.inError()) {
                 valid = false;
             } else {

                 var sDateTime = Util.parseJSDateTime(this.startDate.get(), IndicoDateTimeFormats.Server);
                 var eDateTime = Util.parseJSDateTime(this.endDate.get(), IndicoDateTimeFormats.Server);
                 var minDate = new Date('1901-12-13 21:45:52+00:00');
                 var maxDate = new Date('2038-01-19 04:14:07+00:00');
                 if (sDateTime >= eDateTime) {
                     valid = false;
                     this.startDate.setError($T('Start date should be before end date'));
                     this.endDate.setError($T('End date should be after start date'));
                 } else {
                    if (sDateTime < minDate || maxDate < sDateTime) {
                        valid = false;
                        this.startDate.setError($T("The start date is invalid."));
                    }
                    if (eDateTime < minDate || maxDate < eDateTime) {
                        valid = false;
                        this.endDate.setError($T("The end date is invalid."));
                    }
                    if (valid) {
                        this.startDate.setError(null);
                        this.endDate.setError(null);
                    }
                 }
             }

             this._setSave(valid);
         },

         _handleEditMode: function(value) {

             this.shiftTimes = Html.checkbox({});

             // create datefields
             this.startDate = new DateTimeSelector();
             this.endDate = new DateTimeSelector();

             // set them to the values that are passed
             this.startDate.set(Util.formatDateTime(value.startDate, IndicoDateTimeFormats.Server));
             this.endDate.set(Util.formatDateTime(value.endDate, IndicoDateTimeFormats.Server));

             var self = this;

             this.startDate.observe(function() {
                 self.__verifyDates();
                 return true;
             });
             this.endDate.observe(function() {
                 self.__verifyDates();
                 return true;
             });

             // call buildStructure with modification widgets
             return Html.div({},
                             this.__buildStructure(this.startDate.draw(), this.endDate.draw()),
                             (this.showShiftOption ?
                                  Html.div("widgetCheckboxOption",
                                      this.shiftTimes,
                                      Html.span({},
                                      $T("Move session/contribution times in the timetable accordingly")))
                                  : ''
                              ));
         },

         _handleDisplayMode: function(value) {
             // call buildStructure with spans
             return this.__buildStructure(
                 Util.formatDateTime(value.startDate),
                 Util.formatDateTime(value.endDate));
         },

         _getNewValue: function() {
             return {startDate: Util.parseDateTime(this.startDate.get(),
                                                   IndicoDateTimeFormats.Server),
                     endDate: Util.parseDateTime(this.endDate.get(),
                                                 IndicoDateTimeFormats.Server),
                     shiftTimes: this.shiftTimes
                     };
         },

         _verifyInput: function() {
             if (!Util.parseDateTime(this.startDate.get())) {
                 return false;
             } else if (!Util.parseDateTime(this.endDate.get())){
                 return false;
             }
             return true;
         }
     },
     function(method, attributes, initValue, showShiftOption) {
         this.showShiftOption = showShiftOption;
         this.InlineEditWidget(method, attributes, initValue);
     });


/*
 * A widget that contains a DateTimeSelector and a duration field
 */
type("DateTimeDurationWidget", ["IWidget"],
     {
         draw: function() {
             this.dateTimeField = new DateTimeSelector({});

             $B(this.dateTimeField, this.data.accessor('dateTime'));

             return Html.div(
                 {},
                 Html.label("fieldLabel", this.dateTimeLabel),
                 this.dateTimeField.draw(),
                 Html.span({style:{marginLeft: pixels(10)}},""),
                 Html.label("fieldLabel", this.durationLabel),
                 $B(IndicoUI.Widgets.Generic.durationField(),
                    this.data.accessor('duration')));
         },
         set: function(property, value) {
             this.data.set(property, value);
         },
         accessor: function(property) {
             return this.data.accessor(property);
         }
     },

     /*
      * There are 2 optional labels:
      * - One before the date/time field.
      * - One before the duration field.
      * All 4 element (the 2 fields and the 2 labels) appear in a line.
      * @param {String} defaultDateTime Date formatted like %d/%m/%Y %H:%M (python format)
      * @param {String} defaultDur a duration (for ex: 20)
      * @param {String} dateTimeLabel
      * @param {String} durationLabel
      */
     function(defaultDateTime, defaultDur, dateTimeLabel, durationLabel) {
         this.dateTimeLabel = dateTimeLabel || $T("Date/Time:");
         this.durationLabel = durationLabel || $T("Duration(min):");

         this.data = new WatchObject();
         this.data.set('dateTime', defaultDateTime);
         this.data.set('duration', defaultDur);
     });

/*
 * A DateTimeSelector that keeps its data saved in hidden fields
 * (ideal for form submissions, etc...)
 */
type("DateTimeSelectorWFields", ["DateTimeSelector"],
     {
         _setHiddenFields: function(value) {
             var dtValue = Util.parseJSDateTime(value, IndicoDateTimeFormats.Server);

             if (!dtValue) {
                 // in case the value can't be parsed, set it to empty
                 each(this._fields, function(fname) {
                     $E(fname).set('');
                 });
                 return;
             }

             $E(this._fields[0]).set(dtValue.getDate());
             $E(this._fields[1]).set(dtValue.getMonth() + 1);
             $E(this._fields[2]).set(dtValue.getFullYear());

             if (!this._dateOnly) {
                 $E(this._fields[3]).set(dtValue.getHours());
                 $E(this._fields[4]).set(dtValue.getMinutes());
             }
         }
     },
     // fields : array: d m y [H M]
     // dateOnly: true if no hour is to be passed
     function(args, format, mandatory, dateOnly, fields) {
         this.DateTimeSelector(args, format, mandatory);
         this._fields = fields;
         this._dateOnly = dateOnly;

         var self = this;

         // on change, update hidden fields
         this.observe(function(value) {
             self._setHiddenFields(value)
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
