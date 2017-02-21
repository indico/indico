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
     @namespace Complete widgets for use in the interface
    */
IndicoUI.Widgets = {
    /**
        * Creates a dynamic "keyword list".
        * The widget will have a Save button if the argument 'method' is not empty.
        * @param {Object} kindOfList How the list is displayed. Currently 2 are supported 'oneLineListItem' and 'multipleLinesListItem'.
        * This is done through CSS (see Default.css).
        * @param {Object} method The mapping for the indico Service to be called.
        * @param {Object} attributes The attributes that will be passed to the method.
        * @param {Object} handler A function(result,error) to be called after values are saved.
        * Leave empty to display 'Saved' next to the Save button.
        * @return An object with the 'element' and 'accessor' properties.
        *         The former contains the DOM element (XElement), while the
        *         latter, the accessor to the data.
        */
    keywordList: function(kindOfList, method, attributes, handler, icontitle) {
        var list = new WatchList();

         var image = Html.img({
                src: imageSrc("remove"),
                alt: 'Remove status',
                title: $T('Remove this status from the list')
            });

        var getElement = function() {
            var text = Html.edit();
            var buttonBlock;
            var message = Html.span({style: {marginLeft: '5px'}});

            var addButton = Html.input('button','popUpButton',$T('Add'));
            addButton.observeClick(function(){
                var elem = text.get();
                if (!search(list,match(elem)) && elem !== '') {
                    list.append(elem);
                    text.set('');
                    message.set('');
                }
            });

            if (!handler) {
                handler = function(result, error){
                    if (error) {
                        message.set('Error');
                        message.dom.style.color='red';
                    } else {
                        message.set('Saved');
                        message.dom.style.color='green';
                    }
                };
            }

            if (method) {
                var saveButton = Html.input('button','popUpButton',$T('Add'));
                /* before the value was 'Save', now it is changed because of Paper Reviewing Module
                If in future it is needed to be 'Save' again, we should add one more button and to be choosen between the two */
                saveButton.observeClick(function(){
                    var elem = text.get();
                if (!search(list,match(elem)) && elem !== '') {
                    list.append(elem);
                    text.set('');
                    message.set('');
                }
                    indicoRequest(method,extend(clone(attributes), {'value': list}),handler);
                });
                buttonBlock = Widget.inline([saveButton]);
            } else {
                buttonBlock = Widget.inline([addButton]);
            }

            var wordList = Html.div({style: {width: '300px', overflow: 'auto'}});

            return Widget.block([
                Widget.block([Html.label($T('Keywords:')), text, buttonBlock,message, $B(wordList, list.length, function(length) {
                    return length === 0 ? Html.div({style:{height: pixels(25),
                                                           margin: pixels(5),
                                                           fontStyle: 'italic'}}, $T("No items")):$B(Html.ul("keywordList"), list,
                                                                                                 function(value, index) {
                                                                                                     var style =  index == (list.length.get()-1) ? kindOfList+"_last" : kindOfList ;
                                                                                                     return Html.li(style,[value, Widget.link(command(
                                                                                                         function() {
                                                                                                             list.remove(value);
                                                                                                             var elem = text.get();
																							                 if (!search(list,match(elem)) && elem !== '') {
																							                    list.append(elem);
																							                    text.set('');
																							                }
																							                 indicoRequest(method,extend(clone(attributes), {'value': list}),handler);
                                                                                                             message.set('');
                                                                                                         },
                                                                                                          Html.span({style: {marginLeft: '5px'}}, Html.img({style:{verticalAlign:"bottom", width:'15px', height:'15px'},src: imageSrc("remove"), title: icontitle}))))]);
                                                                                                 });
                })])
            ]);
        };

        return {
            element: getElement(),
            accessor: list
        };
    },

    /**
        @namespace Generic, resusable, components
        */
    Generic: {

        /**
         * (DEPRECATED)
         * Creates a tooltip above the given element.
         * Example of usage:
         *
         * var homeButtonPopup = function(event) {
         *     IndicoUI.Widgets.Generic.tooltip(this, event, "<span style='padding:3px'>Go to Indico Home Page</span>");
         * }
         * $E('homeButton').dom.onmouseover = homeButtonPopup;
         *
         * @param {Object} in_this (view example)
         * @param {Object} event (view example)
         * @param {String} content Whatever content is desired.
         */
        tooltip: function(in_this, event, content) {
            var $this = $(in_this);
            if($this.data('hasTooltip')) {
                return;
            }
            $this.data('hasTooltip', true).qtip({
                content: {
                    text: content
                },
                show: {
                    ready: true
                }
            });

            // Return the onmouseout handler in case
            // it needs to be called from outside
            return function() {
                $this.qtip('hide');
            };
        },

        /**
         * Adds a calendar widget to a text input element.
         * @param {XElement} elem The input element
         * @param {Boolean} showTime true to show hours and minutes, false for only date
         * @param {Array or String} hiddenFields An array of 5 field ids where the day/month/year/hours/minutes will be written,
         *                                       or a single element id where the full string will be put.
         * @param {XElement} trigger Input element triggering calendar (optional).
         * @param {String} format Format for displaying and parsing the date/time (optional).
         */
        input2dateField: function(elem, showTime, hiddenFields, trigger, format) {
            if (showTime === undefined) {
                showTime = false;
            }

            elem.processDate = function(){
                var d;
                if (showTime) {
                    if (exists(format)) {
                        d = Util.parseJSDateTime(elem.get(), format);
                    } else {
                        d = IndicoUtil.parseDateTime(elem.get());
                    }
                } else {
                    if (exists(format)) {
                        d = Util.parseJSDateTime(elem.get(), format);
                        if (d != null) {
                            d = getDate(d);
                        }
                    } else {
                        d = parseDate(elem.get());
                    }
                }

                var ret = false;
                if (d) {
                    if (isArray(hiddenFields)) {
                        $E(hiddenFields[0]).set(!showTime?d[0]:d.getDate());
                        $E(hiddenFields[1]).set(!showTime?d[1]:d.getMonth() + 1);
                        $E(hiddenFields[2]).set(!showTime?d[2]:d.getFullYear());
                        if (showTime) {
                            $E(hiddenFields[3]).set(d.getHours());
                            $E(hiddenFields[4]).set(d.getMinutes());
                        }
                    } else if (hiddenFields) {
                        $E(hiddenFields).set(elem.get());
                    }
                    ret = true;
                } else {
                    if (isArray(hiddenFields)) {
                        $E(hiddenFields[0]).set('');
                        $E(hiddenFields[1]).set('');
                        $E(hiddenFields[2]).set('');
                        if (showTime) {
                            $E(hiddenFields[3]).set('');
                            $E(hiddenFields[4]).set('');
                        }
                    } else if (hiddenFields) {
                        $E(hiddenFields).set('');
                    }
                }

                return ret;
            };

            if (hiddenFields) {
                elem.observe(elem.processDate);
            }

            if (!exists(format)) {
                if (showTime) {
                    format = "%d/%m/%Y %H:%M";
                } else {
                    format = "%d/%m/%Y";
                }
            }

            var onSelect = function(cal) {
                var p = cal.params;
                var update = (cal.dateClicked || exists(cal.activeDiv._range)); // if there is _range we are updating the time
                if (update && p.inputField) {
                    p.inputField.value = cal.date.print(p.ifFormat);
                    $(p.inputField).trigger('change');
                }
                if (update && p.displayArea)
                    p.displayArea.innerHTML = cal.date.print(p.daFormat);
                if (update && typeof p.onUpdate == "function")
                    p.onUpdate(cal);
            };

            Calendar.setup({
                inputField: elem.dom,
                button: trigger == undefined ? elem.dom : trigger.dom,
                displayArea: elem,
                align: "",
                eventName: "click",
                ifFormat: format,
                showsTime: showTime,
                onSelect: onSelect
            });

        },

        /**
         * Creates an input text element with a calendar attached.
         * For this, it uses input2dateField.
         * @param {Boolean} showTime true to show hours and minutes, false for only date
         * @param {Object} attributes An object / dictionary with the attributes of the returned element.
         * @param {Array or String} hiddenFields An array of 5 field ids where the day/month/year/hours/minutes will be written,
         *                                       or a single element id where the full string will be put.
         * @param {Dictionary} elemInfo Additional parameters attached to the input element (optional).
         * @return {XElement} The text input field with the calendar attached.
         */
        dateField: function(showTime, attributes, hiddenFields, elemInfo, format, callback){
            attributes = attributes || {};
            elemInfo = elemInfo || {};
            extend(elemInfo, attributes);
            var elem = Html.input("text",elemInfo);
            var trigger = Html.img({src: imageSrc("calendarWidget")});
            var tab = Html.div("dateField", elem, trigger);

            IndicoUI.Widgets.Generic.input2dateField(elem, showTime, hiddenFields, trigger, format);

            elem.set("");
            //Redirecting method invocation from 'tab' to 'elem'
            tab.set = function(string){
                elem.set(string);
            };
            tab.get = function(){
                return elem.get();
            };
            tab.observe = function(fun){
                elem.observe(fun);
            };
            tab.observeChange = function(fun){
                elem.dom.onchange = fun;
            };
            tab.dom.onchange = function(){
                if(typeof(elem.dom.onchange) === 'function') {
                    elem.dom.onchange();
                }

                if (callback !== undefined) {
                    callback();
                }
            };
            tab.processDate = elem.processDate;

            return tab;
        },

        dateField_sdate: function(showTime, attributes, hiddenFields){
            return IndicoUI.Widgets.Generic.dateField(showTime, attributes, hiddenFields, {'id':'sdate', 'name':'sdate'});
        },

        dateField_edate: function(showTime, attributes, hiddenFields){
            return IndicoUI.Widgets.Generic.dateField(showTime, attributes, hiddenFields, {'id':'edate', 'name':'edate'});
        }
    }
};


