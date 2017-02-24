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


/**
 @namespace Utility functions for IndicoUI
*/

var IndicoUtil = {

    /**
    * Creates a new DOM-based HTML form from a map specification.
    * @param {List} map A map, conforming to the described format
    * @return An element (DIV) containing the form
    */
    createFormFromMap: function(map, expand) {
        expand = any(expand, false);
        var labelStyle = "style='text-align: right; vertical-align: top;'";
        var fieldStyle = "style='vertical-align: top;'";
        if (expand) {
            labelStyle = "style='white-space:nowrap;'";
            fieldStyle = "style='width:100%;'";
        }
        var table = $("<table></table>");
        $(map).each(function(key, item) {
            // if the key is an int, do not print the label
            if (item.length == 2) {
                // TO REMOVE: when completed migration to jquery
                if(!item[1].jquery && item[1].dom) item[1] = $(item[1].dom);

                var row = $("<tr style='margin-top:10px;'></tr>");
                row.append($("<td " + labelStyle + "><label class='popUpLabel'>" + item[0] +"</label></td>"));
                row.append($("<td " + fieldStyle + "></td>").append($("<div class='popUpTdContent'></div>").append(item[1])));
                table.append(row);
            } else {
                // TO REMOVE: when completed migration to jquery
                if(item[0]!== undefined && !item[0].jquery && item[0].dom) item[0] = $(item[0].dom);

                table.append($("<tr style='margin-top:10px;'><td></td></tr>").append($("<td " + fieldStyle + "></td>").append(item[0])));
            }
        });
        return table

    },


    /**
    * Formats a JS Date, returning a string (DD/MM/YY HH:MM)
    * @param {Date} date A JS Date
    * @param {Integer} weekDayOption If different from 0, will add the weekday in different ways.
    * @return A string representation of the Date object
    */
    formatDateTime: function(date, weekDayOption) {
        if (!exists(weekDayOption)) {
            weekDayOption = 0;
        }

        var dateText = zeropad(date.getDate())+'/'+ zeropad(date.getMonth()+1) +'/'+date.getFullYear()+' '+ zeropad(date.getHours())+':'+zeropad(date.getMinutes());

        switch(weekDayOption) {
        case 1:
            return Indico.Data.WeekDays[date.getDay()] + " " + dateText;
        case 2:
            return Indico.Data.WeekDays[date.getDay()].substring(0,3) + " " + dateText;
        case 3:
            return dateText + " (" + Indico.Data.WeekDays[date.getDay()] + ")";
        case 4:
            return dateText + " (" + Indico.Data.WeekDays[date.getDay()].substring(0,3) + ")";
        default:
            return dateText;
        }
    },

    /**
    * Formats a JS Date, returning a string (DD/MM/YY)
    * @param {Date} date A JS Date
    * @return A string representation of the Date object
    */
    formatDate: function(date) {
        return zeropad(date.getDate())+'/'+ zeropad(date.getMonth()+1) +'/'+date.getFullYear();
    },

    /**
    * Formats a JS Date, returning a string (YYYYMMDD)
    * @param {Date} date A JS Date
    * @return A string representation of the Date object
    */
    formatDate2: function(date) {
        return '' + date.getFullYear() + zeropad(date.getMonth()+1) + zeropad(date.getDate());
    },

    /**
    * Parses a string (DD/MM/YY HH:MM) into a JS Date, returning a string
    * @param {String} strDateTime A string representation of the date/time
    * @return A JS Date with the parsed date/time
    */
    parseDateTime: function(strDateTime) {
        strDateTime = strDateTime.split(' ');
        if (strDateTime.length != 2) {
            return null;
        }

        var sdate = parseDate(strDateTime[0]);
        var stime = parseTime(strDateTime[1]);

        if ( !sdate || !stime) {
            return null;
        }

        var sdatetime = new Date(sdate[2], sdate[1]-1, sdate[0]);
        setTime(sdatetime, stime);

        return sdatetime;
    },

    parseDate: function(strDate) {

        var sdate = parseDate(strDate);

        if ( !sdate ) {
            return null;
        }

        var sdatetime = new Date(sdate[2], sdate[1]-1, sdate[0]);
        setTime(sdatetime, [0,0,0,0]);


        return sdatetime;
    },

    /**
    * Parses a json date object into a JS Date
    * @param {Dictionary} A dictionary with date and time keys set
    * @return A JS Date with the parsed date/time
    */
   parseJsonDate: function(date) {
       var year = parseInt(date.date.substr(0,4), 10);
       var month = parseInt(date.date.substr(5,2), 10);
       var day = parseInt(date.date.substr(8,2), 10);

       var hour = parseInt(date.time.substr(0,2), 10);
       var min = parseInt(date.time.substr(3,2), 10);

       return new Date(year, month-1, day, hour, min);
   },

    /**
     *
     */
    isInteger: function(s) {

        var isEmpty = function(s) {
            return (!exists(s) || (s.length === 0));
        };

        var isDigit = function(c) {
            return ((c >= "0") && (c <= "9"));
        };

        var i;

        if (isEmpty(s)) {
            return false;
        }

        for (i = 0; i < s.length; i++) {
            var c = s.charAt(i);
            if (!isDigit(c)) {
                return false;
            }
        }
        return true;
    },


    /**
     * Determines if a string is in a valid time format (hh:mm)
     * @param {String} s The input string
     * @return {Booleab} true if the string is a valid time string, false otherwise
     */
    isTime: function(s) {
        var regExp = new RegExp("(^([0-9]|[0-1][0-9]|[2][0-3]):([0-5][0-9])$)");
        return regExp.test(s);
    },

    /**
     * Marks an input field (text, checkbox or select) as invalid.
     * It will change its CSS class so that it appears red, and place an error tooltip over it on mouseover.
     * If the value of the field changes / the user types in the field, the red color and the tooltip will disappear
     * @param {XElement} component: the field to mark as invalid
     * @param {XElement} error: the string or Html object that will be displayed in the error popup.
     * @return {[XElement, Array of functions]} returns an array with 2 elements:
     *                                          -An Html.div() XElement with the tooltip that was created.
     *                                          -An array of functions that should be called to cancel all the event observations.
     */
    markInvalidField: function(component, error, passive) {

        // passive - don't check actively for changes / keypresses
        if (component.dom.type) {
            if ( startsWith(component.dom.type, 'select')) {
                if (component.dom.className.slice(-13) != "hasError") {
                    component.dom.className += ' hasError';
                }
            } else {
                if (component.dom.className.slice(-7) != "hasError") {
                    component.dom.className += ' hasError';
                }
            }
        } else {
            if (component.dom.className.slice(-7) != "hasError") {
                component.dom.className += ' hasError';
            }
        }

        var oList = []; //list of functions that we will call to stop observing events

        var stopObserving = function(){
            each(oList, function(value){
                value();
            });
        };

        // we'll add a function that removes the coloring first of all
        oList.push(function() {
            $(component.dom).removeClass('hasError').qtip('destroy');
        });

        $(component.dom).qtip({
            content: {
                text: error.dom ? $(error.dom) : error
            }
        });

        if (!passive) {
            $(component.dom).on('keypress change select click', stopObserving);
        }

        return oList;
    },

    /**
     * Parameter manager.
     * Checks if all the parameters in a form are correct.
     * If not, it sets the input background-color to red and adds a tooltip explaining the error.
     * How to use:
     * 1. make one: pm = parameterManager()
     * 2. add stuff to it: pm.add(Html.edit({style: {width: '300px'}}), 'text', false)
     * 3. make checks: pm.check()
     */
    parameterManager: function() {

        var entryList = new WatchList(); //elements to check
        var classList = {}; //original class (style) value for each element to check
        var eventList = {}; //all the 'error' events for each element to check

        //var radioButtonChecks = {}; //
        var radioButtonLabelStopObserving = {};

        this.clear = function() {
            entryList = new WatchList();
            classList = {};
            eventList = {};
        };

        /**
         * Check entries for errors
         */
        this.check = function() {

            var self = this;
            var hasErrors = false;

            entryList.each(function(value) {

                var component = value[0];
                var dataType = value[1];
                var allowEmpty = value[2];
                var extraCheckFunction = value[3];
                var error = null;

                // ErrorAware classes don't want to do this
                if (component.ErrorAware) {
                    component.setError(false);

                } else {
                    //--- Restore original values (if it is the second time, there must
                    //    be components with error styles)  ---

                    component.dom.className = classList[component.dom.id];

                    if (exists(eventList[component.dom.id])) {
                        // --- Remove all the ERROR observers
                        $L(eventList[component.dom.id]).each(function(value){
                            value();
                        });

                        delete eventList[component.dom.id];
                    }
                    //---------------------------------
                }

                //--- Check if there are errors ---
                if (dataType == "checkBoxList" && !exists(extraCheckFunction)) {
                    if (!allowEmpty && !self.checkCheckBoxes(component)) { // component must be the parent element of all the checkboxes
                        error = Html.span({}, $T("At least one must be selected"));
                    }
                }
                else if (dataType == 'checkBox' && !exists(extraCheckFunction)) {
                    if (!allowEmpty && !component.dom.checked) {
                        error = Html.span({}, $T("Please enable the checkbox"));
                    }
                }
                else if (dataType == "radio" && !exists(extraCheckFunction)) {
                    if (!allowEmpty && !self.checkRadioButton(component)) {
                        error = Html.span({}, $T("Please choose an option"));
                    }
                }
                else if (dataType == "select" && !exists(extraCheckFunction)) {
                    if (!allowEmpty && !self.checkSelect(component)) {
                        error = Html.span({}, $T("Please choose an option"));
                    }
                }
                else if (dataType == 'int' && !(allowEmpty && trim(component.get()) === '') && !IndicoUtil.isInteger(component.get())) {
                    error = Html.span({}, $T("Field must be a number"));
                }
                else if (dataType == 'unsigned_int' && !(allowEmpty && trim(component.get()) === '') && (!IndicoUtil.isInteger(component.get()) || component.get()<=0)) {
                    error = Html.span({}, "Field must be a positive number");
                }
                else if (dataType == 'non_negative_int' && !(allowEmpty && trim(component.get()) === '') && (!IndicoUtil.isInteger(component.get()) || component.get()<0)) {
                    error = Html.span({}, $T("Field must be a positive number"));
                }
                else if (dataType == 'datetime' && !(allowEmpty && trim(component.get()) === '') && !IndicoUtil.parseDateTime(component.get())) {
                    error = Html.span({}, $T("Date format is not valid. It should be dd/mm/yyyy hh:mm"));
                }
                else if (dataType == 'email' && !(allowEmpty && trim(component.get()) === '') && !Util.Validation.isEmailAddress(component.get())) {
                    error = Html.span({}, $T("Invalid e-mail address"));
                }
                else if (dataType == 'url' && !(allowEmpty && trim(component.get()) === '') && !Util.Validation.isURL(component.get())) {
                    error = Html.span({}, $T("Invalid URL"));
                }
                else if (dataType == 'time' && !IndicoUtil.isTime(trim(component.get()))) {
                    error = Html.span({}, $T("Time format is not valid. It should be hh:mm"));
                }
                else if (!allowEmpty && component.get() != null && (!isString(component.get()) || trim(component.get()) === '')) {
                    error = Html.span({}, $T("Field is mandatory"));
                }
                if (exists(extraCheckFunction)) {
                    error = error || extraCheckFunction(component.get());
                }
                //--------------------------------


                //---- Display error -------
                if (exists(error)) {
                    hasErrors = true;

                    var oList;

                    if (component.ErrorAware) {
                        oList = component.setError(error);

                    } else if (dataType == 'checkBoxList' || dataType == 'radio' || dataType == 'select') {
                        oList = IndicoUtil.markInvalidField(component, error);
                    } else if (component.dom.type != 'radio') {
                        oList = IndicoUtil.markInvalidField(component, error);
                    } else {
                        // XXX: Is this code still used anywhere?!
                        // If yes, please add a comment where, if not let's remove it!
                        // The jQuery/qtip things here are untested btw.. if you find out where this is used, please test it. :)
                        var $label = $('#' + component.dom.id + 'Label');
                        var $component = $(component.dom);
                        $label.addClass('invalidLabel');
                        $component.addClass('invalid');
                        $component.add($label).qtip({
                            content: {
                                text: error.dom ? $(error.dom) : error
                            }
                        });

                        var stopObserving = function() {
                            $component.qtip('destroy');
                            $label.qtip('destroy');
                        };
                        oList = [stopObserving]; //list of functions that we will call to stop observing events

                        if (!exists(radioButtonLabelStopObserving[component.dom.name])) {
                            radioButtonLabelStopObserving[component.dom.name] = [];
                        }
                        radioButtonLabelStopObserving[component.dom.name].push(stopObserving);

                        each($N(component.dom.name), function(component){
                            component.observeEvent('click', function(event) {
                                each($N(component.dom.name), function(subcomponent){
                                    $(subcomponent.dom).removeClass('invalid');
                                    $('#' + subcomponent.dom.id + 'Label').removeClass('invalidLabel');
                                });
                                if (exists(radioButtonLabelStopObserving[component.dom.name])) {
                                    each (radioButtonLabelStopObserving[component.dom.name], function(stopObserver) {stopObserver()});
                                }
                            });
                        });
                    }

                    if (!component.ErrorAware) {
                        eventList[component.dom.id] = oList;
                    }
                }
                //----------------------------
            });
            return !hasErrors;
        };

        this.checkRadioButton = function(component) {
            var name = component.dom.name;
            /*if (!exists(radioButtonChecks[name])) {
                radioButtonChecks[name] = false;
                var radioButtons = $N(name);
                each (radioButtons, function(rb) {
                    if (rb.dom.checked) {
                        radioButtonChecks[name] = true;
                    }
                });
            }
            return radioButtonChecks[name];*/
            var radioButtonChecks = false;
            var radioButtons = $N(name);
            each (radioButtons, function(rb) {
                if (rb.dom.checked) {
                    radioButtonChecks = true;
                }
            });
            return radioButtonChecks;
        };

        this.checkSelect = function(component) {
            return (component.dom.value!="")
        };

        // component must be the parent element of all the checkboxes
        this.checkCheckBoxes = function(component) {
            for (var i=0; i<component.dom.childNodes.length; i++) {
                var node = component.dom.childNodes[i];
                if (node.type == "checkbox" && node.checked) {
                    return true;
                }
            }
            return false;
        };

        /**
         * Adds a form input to the list of paramters to check.
         *  @param {Html component} component The input component
         *  @param {String} dataType Type of the data: text, int, date, etc
         *  @param {Boolean} allowEmpty True if the component is mandatory
         *
         */
        this.add = function(component, dataType, allowEmpty, extraCheckFunction) {
            if (component instanceof jQuery) {
                component = $E(component[0]);
            }

            // Add new entry
            entryList.append([component, dataType, allowEmpty, extraCheckFunction]);

            // only for DOM elements
            if (!component.ErrorAware) {
                // Assign an auto ID, if the object has no ID (if it's a DOM element)
                if (!component.dom.id) {
                    component.dom.id = Html.generateId();
                }

                classList[component.dom.id] = component.dom.className;
            }
            return component;
        };

        this.remove = function(component) {
            if (component instanceof jQuery) {
                component = $E(component[0]);
            }

            var removeEntry = null;
            each(entryList,
                 function(entry) {
                     if (entry[0] == component) {
                         removeEntry = entry;
                     }
                 });

            if (removeEntry) {
                entryList.remove(removeEntry);
            }
        };

    },

    /**
     * Adds new function that is to be called when the document.onclick
     * event is triggered.
     * @param {function} f
     */
    onclickHandlerAdd : function(f) {
        IndicoUtil.onclickFunctions.append(f);
    },

    onclickHandlerRemove : function(f) {
        var idx = this.onclickFunctions.indexOf(f);
        this.onclickFunctions.replaceAt(idx, null);
    },

    onclickFunctions : new WatchList(),

    // DEPRECATED, in favor of IndicoUI.Dialogs.Util.error
    errorReport: IndicoUI.Dialogs.Util.error,

    /**
     * Simple function used in sorting
     */
    compare: function(elem1, elem2){
        if(elem1 > elem2)
            return 1;
        if(elem1 < elem2)
            return -1;
        if(elem1 == elem2)
            return 0;
    }
};
