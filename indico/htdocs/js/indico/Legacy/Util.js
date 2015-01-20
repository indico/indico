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


/**
 @namespace Utility functions for IndicoUI
*/

var IndicoUtil = {

    /**
     * Utility function that, given a container element, will look at all of the nodes inside it, and
     * return the list of nodes that are of type "input", "select", and "textArea".
     * @param {multiple XElement} A variable number of XElement's that we want to scan for form-like nodes.
     * @return {Array of DOM nodes} Returns an array of DOM nodes that are of type "input", "select", and "textArea".
     */
    findFormFields : function() {
        var formNodes = [];

        for (var i=0; i < arguments.length; i++) {
            var xelement = arguments[i];

            var inputNodes = xelement.dom.getElementsByTagName("input");
            var selectNodes = xelement.dom.getElementsByTagName("select");
            var textAreaNodes = xelement.dom.getElementsByTagName("textArea");

            for (var j=0; j < inputNodes.length; j++) {formNodes.push(inputNodes[j]);}
            for (var j=0; j < selectNodes.length; j++) {formNodes.push(selectNodes[j]);}
            for (var j=0; j < textAreaNodes.length; j++) {formNodes.push(textAreaNodes[j]);}
        }

        return formNodes;
    },

    /**
    * Utility function that, given a container element, will find the "form" nodes inside it
    * and extract the values from those elements.
    * @param {Array} components An array of input nodes / custom components.
    *                           Nodes can be obtained easily like this: var formNodes = IndicoUtil.findFormFields(containerElement)
    *                           Custom components have to have a .get() and a .getName() method.
    * @param {Object} values An object where there values will be stored; this object will be "cleaned" and then returned.
    *                        If left to null, a new object will be returned.
    * @return {Array} an object whose keys are the "name" attribute of the form nodes, and the values
    *                 are the values of those nodes.
    */
    getFormValues : function(components, values) {
        if (!exists(values)) {
            values = {};
        } else {
            each(values, function(value, key){
                delete values[key];
            });
        }
        for (var i=0; i < components.length; i++) {
            var component = components[i];
            if (isDom(component)) {
                var node = component;
                if (exists(node.name) && node.name) {
                    if (node.type == "checkbox") {
                        if (!exists(values[node.name])) {
                            values[node.name] = [];
                        }
                        if (node.checked) {
                            values[node.name].push(node.value);
                        }
                    } else if (node.type == "radio") {
                        if (node.checked) {
                            values[node.name] = node.value;
                        }
                    } else {
                        values[node.name] = node.value;
                    }
                }
            } else {
                if(exists(component.get) && exists(component.getName)) {
                    values[component.getName()] = component.get();
                }
            }
        }
        return values;
    },

    /**
    * Utility function that, given a container element, and an object with key/value pairs, will find the "form" nodes inside it
    * and put those values in each node. To find the correct node for each value, the "name" attribute of the nodes are compared
    * to the 'keys' of the object.
    * @param {Array} components An array of input nodes / custom components.
    *                           Nodes can be obtained easily like this: var formNodes = IndicoUtil.findFormFields(containerElement)
    *                           Custom components have to have a .get() and a .getName() method.
    * @param {Array} an object whose keys are the "name" attribute of the form nodes, and the values
    *                are the values of those nodes.
    */
    setFormValues : function(components, values) {

        for (var i=0; i < components.length; i++) {
            var component = components[i];
            if (isDom(component)) {
                var node = component;
                if (node.type == "checkbox") {
                    node.checked = node.name in values && exists($L(values[node.name]).indexOf(node.value));
                } else if (node.type == "radio") {
                    node.checked = node.name in values && values[node.name] == node.value;
                } else {
                    node.value = values[node.name];
                }
            } else {
                if(exists(component.set) && exists(component.getName)) {
                    component.set(values[component.getName()]);
                }
            }
        }
    },

    /**
     * Utility function that sets "form" nodes inside an element to disabled.
     * @param {XElement} containerElement An element to scan for form nodes to disable.
     * @param {Boolean} enableDisable true = enable, false = disable
     */
     enableDisableForm : function (containerElement, enableDisable) {
        var nodesToDisable = {button :'', input :'', optgroup :'', option :'', select :'', textarea :''};

        var node, nodes;
        nodes = containerElement.dom.getElementsByTagName('*');
        if (!nodes) return;

        var i = nodes.length;
        while (i--){
            node = nodes[i];
            if ( node.nodeName && node.nodeName.toLowerCase() in nodesToDisable ) {
                node.disabled = !enableDisable;
            }
        }
    },

    /**
    * Given a function 'f', returns another function 'g' that will accept calls of
    * the form 'g(list,arg1,..,argn)', and append f(arg1,...,argn) to list.
    * @param {Function} func The function that will be applied
    * @return The created function
    * @type Function
    */
    appender: function(func){
        function f(list){
            list.append(func.apply(this, Array.prototype.slice.call(arguments, 1)));
        }

        return f;
    },

    /**
    * Changes the style of a CSS class dynamically.
    * WARNING: the cls argument will be converted to lowercase.
    * Due to Firefox storing css names like this: ul.tabList ,
    * and IE7 storing them like this: UL.tabList,
    * the cls argument has to be converted to lowercase.
    * This means that two class names who only differ by lowercase / uppercase
    * will be considered the same.
    * @param {String} cls The name of the class whose style will be changed
    * @param {String} style The new style (CSS)
    */
    changeClassCss: function(cls, style){
        if (!document.styleSheets) {
            return;
        }
        var css;
        if (document.styleSheets[0].cssRules) {
            css = document.styleSheets[0].cssRules;
        }
        else {
            css = document.styleSheets[0].rules;
        }
        for (var i = 0; i < css.length; i++) {
            if (css[i].selectorText.toLowerCase() == cls.toLowerCase()) {
                css[i].style.cssText = style;
            }
        }
    },

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
     * Formats a JS Date, returning just the time as a string (HH:MM)
     * @param {Date} date A JS Date
     * @return A string representation of the Date object
     */
    formatJustTime: function(date) {
        return zeropad(date.getHours())+ ':' +zeropad(date.getMinutes());
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

        var sdatetime = new Date();
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

        var sdatetime = new Date();
        var sdate = parseDate(strDate);

        if ( !sdate ) {
            return null;
        }

        var sdatetime = new Date(sdate[2], sdate[1]-1, sdate[0]);
        setTime(sdatetime, [0,0,0,0]);


        return sdatetime;
    },

    /**
     * Formats a datetime object with 2 attributes, .date and .time
     * (obtained by pickling with Conversion.datetime)
     */
    formatJsonDate: function(jsonDate) {
        return jsonDate.date + ' at ' + jsonDate.time.substring(0,5);
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

    cachedRpcValue: function(endPoint, method, attributes, cachedValue) {

        if (exists(cachedValue)) {
            var self;
            self = new WatchValue();
            self.set(cachedValue);

            self.observe(function(value) {
                jsonRpcCommit(endPoint, method, attributes, value,
                              function(result, error) {
                                  if(exists(error)) {
                                      IndicoUtil.errorReport(error);
                                      self.set(cachedValue);
                                  } else {
                                      cachedValue = value;
                                      if (exists(result.hasWarning) && result.hasWarning === true) {
                                          var popup = new WarningPopup(result.warning.title, result.warning.content);
                                          popup.open();
                                      }
                                      // would loop infinitely
                                      // self.set(result);
                                  }
                              });
            });
            return self;
        } else {
            return jsonRpcValue(endPoint, method, attributes);
        }

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
     * Determines if a string contains invalid characters for short URLs
     * @param {String} s The input string
     * @return {Boolean} true if the string is a valid string, false otherwise
     */
    parseShortURL: function(s) {
        if (/^[0-9]+$/.test(s)) {
            // Just a number
            return false;
        }
        if (s.substr(0, 1) == '/' || s.substr(s.length - 1, 1) == '/' || ~s.indexOf('//')) {
            // Leading/trailing/duplicate slash
            return false;
        }
        // Restrict characters
        return /^[a-zA-Z0-9/._-]*$/.test(s);
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
                if (component.dom.className.slice(-13) != "invalidSelect") {
                    component.dom.className += ' invalidSelect';
                }
            } else {
                if (component.dom.className.slice(-7) != "invalid") {
                    component.dom.className += ' invalid';
                }
            }
        } else {
            if (component.dom.className.slice(-7) != "invalid") {
                component.dom.className += ' invalid';
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
            component.dom.className = component.dom.className.substring(0, component.dom.className.length-8);
            $(component.dom).qtip('destroy');
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
     *  Used as extraCheckFunction within the parameter manager.
     *  Extra checking for numbers (minimum, maximum).
     *
     */
    validate_number: function(opts) {
        return function(value) {
            var val = parseInt(value, 10);
            if(opts.minimum && val < opts.minimum) return Html.span({}, $T("The value must be at least ") + opts.minimum);
            if(opts.maximum && val > opts.maximum) return Html.span({}, $T("The value must be at maximum ") + opts.maximum);
        }
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
                // TODO: to be replaced by just 'int'
                else if (dataType == 'int_pos_or_neg' && !(allowEmpty && trim(component.get()) === '') && !IndicoUtil.isInteger(component.get())) {
                    if (!(component.get()[0] == '-' && IndicoUtil.isInteger(component.get().slice(1)))) {
                        error = Html.span({}, $T("Field must be a number"));
                    }
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
                else if (dataType == 'emaillist' && !(allowEmpty && trim(component.get()) === '') && !Util.Validation.isEmailList(component.get())){
                    error = Html.span({}, $T("List contains invalid e-mail address or invalid separator"));
                }
                else if (dataType == 'url' && !(allowEmpty && trim(component.get()) === '') && !Util.Validation.isURL(component.get())) {
                    error = Html.span({}, $T("Invalid URL"));
                }
                else if (dataType == 'ip' && !(allowEmpty && trim(component.get()) === '') &&  !Util.Validation.isIPAddress(component.get())) {
                    error = Html.span({}, $T("That doesn't seem like a valid IP Address. Example of valid IP Address: 132.156.31.38"));
                }
                else if (dataType == 'time' && !IndicoUtil.isTime(trim(component.get()))) {
                    error = Html.span({}, $T("Time format is not valid. It should be hh:mm"));
                }
                else if (dataType == 'shortURL' && !IndicoUtil.parseShortURL(component.get())) {
                    error = Html.span({}, $T("The short URL contains invalid characters. The allowed characters are alphanumeric, /, _, - and ."));
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

    waitLoad : function(preLoad, process) {

        var counter = preLoad.length;

        var retVal = new WatchValue();

        var run = (counter===0)?
            curry(process, retVal):
            function() {
                $L(preLoad).each(function(value) {

                    var hook = new WatchValue();
                    hook.set(false);

                    hook.observe(function(value){
                        if (value) {
                            bind.detach(hook);
                            counter--;

                            if (counter === 0) {
                                process(retVal);
                            }
                        }
                    });

                    value(hook);
                });
            };

        return {'returnValue': retVal,
                'run': run };
    },

    detectTextFormat : function(text) {
        if (/<.*>.*<\/.*>/.exec(text)) {
            return "html";
        } else {
            return "plain";
        }
    },

    /**
     * Sorts a watchList by using the watchList clear() and appendMany() methods.
     * Thus, changes in the watchList are notified, but it is an inefficient way
     * of ordering a watchList.
     * If one day the watchList class gets a good sort() method then
     * this should be deprecated.
     * @param {WatchList} watchList
     */
    sortWatchList : function(watchList) {
        var old = watchList.clear();
        var sortedItems = old.sort();
        watchList.appendMany(sortedItems);
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
