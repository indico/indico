/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
         @namespace Widgets that handle personal options
       */
    Options:
    {
        /**
        * Sets the 'advanced tabs' feature on/off
        * @param {Boolean} state The value that the property
        * should be set to
        * @param {Function} handler The callback that will be
        * invoked in case of success
        */
        setAdvancedOptions: function(state, handler){
            jsonRpc(Indico.Urls.JsonRpcService, 'user.personalinfo.set', {
                'value': {
                    'tabAdvancedMode': state
                }
            }, function(response, error){
                if (exists(error)) {
                    IndicoUtil.errorReport(error);
                }
                else {
                    handler();
                }
            });
        }
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


        simpleButton: function(elem, method, attributes, handler, caption) {
            var button = Widget.button(command(function(){
                indicoRequest(method, attributes, handler);
            },caption));
            elem.set(button);
            return button;
        },

        selectionField: function(elem, method, attributes, options, cachedValue, observer){
            elem.set(new SelectEditWidget(method, attributes, options, cachedValue, observer).draw());
        },

        textField: function(elem, method, attributes, cachedValue, observer){
            elem.set(new InputEditWidget(method, attributes, cachedValue, true, observer).draw());
        },

        /**
             * Creates a keyword field that will:
             * -Load a list of values from the server when it is displayed.
             * -Save the list of values when the 'Save' button is pressed.
             * @param {Object} element The DOM element where we want to put the widget.
             * @param {Object} kindOfList How the list is displayed. Currently 2 are supported 'oneLineListItem' and 'multipleLinesListItem'.
             * This is done through CSS (see Default.css).
             * @param {Object} method The mapping for the indico Service to be called.
             * @param {Object} attributes The attributes that will be passed to the method.
             * @param {Object} handler A function that will be called after values are saved.
             * Leave empty to display 'Saved' next to the Save button.
             */
        keywordField: function(element, kindOfList, method, attributes, icontitle, handler) {

            var keywordList = IndicoUI.Widgets.keywordList(kindOfList, method, attributes, handler, icontitle);

            indicoRequest(method,
                          attributes,
                          function(result, error){
                              if (!error) {
                                  each(result, function(value) {
                                      keywordList.accessor.append(value);
                                  });
                              }
                          });

            element.set(keywordList.element);
            return keywordList;
        },

        /**
             * Creates a field made of several radio buttons.
             * The initial value has to be provided at the time the widget is loaded.
             * When the 'Save' button is pressed, the value will be saved.
             * @param {Object} element The DOM element where we want to put the widget.
             * @param {String} kind How the radio buttons are displayed.
             * If 'vertical' is selected, each radio button will appear in a different line (and the 'Save' button under them).
             * If 'horizontal1' is selected, all radio buttons will appear in a line with their labels at their side.
             * If 'horizontal2' is selected, all radio buttons will appear in a line, with the labels on top of them.
             * @param {List of Strings} options A list of the values for the radio buttons. The length of this list determines the number of radio buttons.
             * @param {List of Strings} labels A list of labels for the radio buttons.
             * @param {String} initialValue The radio button that will be initially selected. Leave to false to retrieve it from the server with an AJAX call
             * @param {String} method The mapping for the indico Service to be called.
             * @param {Dictionary} attributes The attributes that will be passed to the method.
             * @param {Function} handler A custom function that will be called after values are saved. It will receive 2 arguments, 'result' and 'error'
             */
        radioButtonField: function(element, kind, options, labels, initialValue, method, attributes, handler) {

            var groupName = Html.generateId(); // The common name for all the radio buttons
            var t; //stores a timeout

            // Utility function for retrieving the selected radio button
            var radioGroupValue = function(groupName, length){
                for (var i = 0; i < length; i++) {
                    if ($E(groupName+ "_" + i).get()) {
                        return $E(groupName+ "_" + i).dom.value;
                    }
                }
                return false;
            };

            var message = Html.span({style: {marginLeft:'5px'}},'\u00A0'); //zone where 'Saved' Or 'Error' will be displayed
            message.dom.id = "message" + groupName; //we assign a unique id to the span object so that we can clear it later

            //function that updates the message zone after an update and clears it later
            var messageUpdater = function(result, error){
                if (error) {
                    message.set('Error');
                    message.dom.style.color='red';
                } else {
                    message.set('Updated');
                    message.dom.style.color='green';
                }
                if (t) {
                    clearTimeout(t);
                }
                t = setTimeout("$E(\""+"message" + groupName + "\").set(\'\u00A0\')",2000);
            };

            // Function to be executed after saving. Currently calls 'messageUpdater' and then custom handler
            var returnHandler = function(result, error){
                messageUpdater(result,error);
                if (handler) {
                    handler(result, error);
                }
            };

            // Function to be executed when a radio button is clicked
            var buttonClicked = function(){
                message.set($T('Updating...'));
                message.dom.style.color='orange';
                indicoRequest(method,
                              extend(clone(attributes), {'value': radioGroupValue(groupName, options.length)}), returnHandler);
            };

            var radioButtons = []; // List of radio buttons

            for (var i=0; i<options.length; i++) {
                // For every option we create a radio button
                var rb = Html.radio({
                    name: groupName,
                    id: groupName + "_" + i
                });
                rb.dom.value = options[i]; //For some reason we have to set the value like this and not in the constructor for it to work in IE
                rb.observeClick(buttonClicked);
                radioButtons.push(rb);
            }

            Logic.onlyOne(radioButtons, false); //Ensures that only 1 radio button will be selected at a given time

            if (initialValue) {
                for (var j=0; j<options.length; j++) {
                    // We mark as checked the radio button corresponding to 'initialValue' if there is one
                    if (options[j] == initialValue) {
                        radioButtons[j].dom.defaultChecked = true; //defaultChecked instead of checked seems to do the trick for IE7
                    }
                }
            } else { // if there is no initial value, we retrieve it from the server and set the appropiate radio button to checked
                var initialValueHandler = function(result,error) {
                    if (!error) {
                        radioButtons[result].dom.checked = true;
                    }
                };
                indicoRequest(method, attributes,initialValueHandler);
            }


            if (kind == "vertical" || kind == "horizontal1") {
                var itemsList = []; // List of HTML elements to be included in the widget block
                for (var k = 0; k < radioButtons.length; k++) {
                    itemsList.push(radioButtons[k]); //We add a radio button
                    itemsList.push(Html.label({
                        htmlFor: groupName + "_" + k
                    }, labels[k])); //We add its corresponding label
                    if (kind == "vertical" && k != radioButtons.length-1) { //if the kind of widget is 'vertical', we add a break line
                        itemsList.push(Html.br());
                    }
                }
                itemsList.push(message);
                var block = Widget.block(itemsList); // We build the block
                if (element) {
                    element.set(block);
                }
                return block;

            }
            else if (kind == "horizontal2") { //in this case we build a table of 2 rows
                var table = Html.table();
                table.dom.style.display = 'inline';
                var tbody = Html.tbody();
                table.set(tbody);

                var row1 = Html.tr();
                var row2 = Html.tr();

                for (var l = 0; l < radioButtons.length; l++) {
                    var cell1 = Html.td();
                    cell1.dom.vAlign = 'bottom';
                    cell1.dom.align = 'center';
                    cell1.append(Html.label({
                        htmlFor: groupName + "_" + l
                    }, labels[l]));
                    row1.append(cell1);

                    var cell2 = Html.td();
                    cell2.append(radioButtons[l]);
                    row2.append(cell2);
                }

                var cellMessage = Html.td();
                cellMessage.dom.style.verticalAlign = "middle";
                cellMessage.dom.rowSpan = 2;
                cellMessage.append(message);
                row1.append(cellMessage);

                tbody.append(row1);
                tbody.append(row2);

                if (element) {
                    element.set(table);
                }

                return table;
            }
            else {
                new AlertPopup($T("Developer error"), $T("Kind of radioButtonField is not correct, should be 'vertical', 'horizontal1', 'horizontal2'")).open();
            }

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
        },

        timeField: function(attributes, hiddenFields){
            attributes = attributes || {};
            return Html.input("text", attributes);
        },

        dateEditor: function(elem, method, attributes, cachedValue){

            IndicoUI.Effect.mouseOver(elem.dom);

            var context = new WidgetEditableContext();

            var editable = new WidgetEditable(WidgetEditable.getClickableView(WidgetEditable.getTemplatedTextView(getBlankTemplate(Html.span({
                style: {
                    fontStyle: 'italic'
                }
            }, "None")))), WidgetEditable.getFieldEditor(curry(IndicoUI.Widgets.Generic.dateField, true)));

            $B(elem, [editable(IndicoUtil.cachedRpcValue(Indico.Urls.JsonRpcService, method, attributes, cachedValue), context), Widget.text(" "), IndicoUI.Aux.defaultEditMenu(context)]);
        },

        dateStartEndTimeField: function(defaultStartTime, defaultEndTime, attributesStartTime, attributesEndTime, additional) {

            var obj = new WatchObject();
            obj.set('startTime', defaultStartTime);
            obj.set('endTime', defaultEndTime);

            var dash = Html.span({style: {padding: '0 10px'}});
            dash.dom.innerHTML = '&ndash;';

            var startTimeField = IndicoUI.Widgets.Generic.timeField(attributesStartTime);
            var endTimeField = IndicoUI.Widgets.Generic.timeField(attributesEndTime);

            var element = Widget.block([
                $B(startTimeField, obj.accessor('startTime')), dash,
                $B(endTimeField, obj.accessor('endTime')),
                additional || ''
            ]);

            return {'element': element,
                    'accessor': obj,
                    'startTimeField': startTimeField,
                    'endTimeField': endTimeField};
        },

        durationField: function(defaultVal, attributes) {
            // TODO: Add value type checking
            attributes = attributes || {};
            attributes.style = {width: '40px'};
            return Html.edit(attributes, defaultVal);
        },
    }// end of Generic namespace

};


