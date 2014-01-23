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


//Widget to change the scale in abstract reviewing
type("ScaleEditWidget", ["InlineEditWidget"],
        {
            /* builds the basic structure for both display and
               edit modes */

            __buildStructure: function(minValue, maxValue, warning) {

                var div = Html.div({style:{paddingLeft:'2px'}});
                var spanTitle = Html.span({className:'dataCaptionFormat'},"Scale for each answer: ");
                var structure = Html.table({},
                                    Html.tbody({},
                                        Html.tr({},Html.td("supportEntry", "From :"),
                                            Html.td({}, minValue)),
                                        Html.tr({},Html.td("supportEntry", "To :"),
                                            Html.td({}, maxValue))));
                div.append(spanTitle);
                div.append(structure);
                if (warning) { // edit mode
                    div.append(warning);
                }
                return div;
            },

            _handleEditMode: function(value) {
                // create the fields
                this.min = Html.edit({size: 2}, value.min);
                this.max = Html.edit({size: 2}, value.max);
                this.warning = Html.div({className:'changeScaleWarning'}, "Please note that when the scale is changed all the previous ratings are set to the new scale values.");
                // add the fields to the parameter manager
                this.__parameterManager.add(this.min, 'int_pos_or_neg', false);
                this.__parameterManager.add(this.max, 'int_pos_or_neg', false);
                // call buildStructure with modification widgets
                return this.__buildStructure(this.min, this.max, this.warning);
            },

            _handleDisplayMode: function(value) {
                // call buildStructure
                return this.__buildStructure(value.min, value.max, null);
            },

            _getNewValue: function() {
                return {min: this.min.get(),
                        max: this.max.get()};
            },

            _verifyInput: function() {
                if (!this.__parameterManager.check()) {
                    return false;
                }
                if (parseInt(this.min.dom.value) >= parseInt(this.max.dom.value)) {
                    new AlertPopup($T("Warning"), $T("The \"From\" value must be lower than \"To\" value.")).open();
                    return false;
                } else if ((parseInt(this.max.dom.value) - parseInt(this.min.dom.value)) > 100) {
                    new AlertPopup($T("Warning"), $T("The maximun difference between limits is 100 units.")).open();
                    return false;
                }
                return true;
            },

            _handleSuccess: function() {
                // previewQuestion is a global var used in ConfModifAbstractRev
                previewQuestion.draw();
            }
        },
        function(method, attributes, initValue) {
            this.InlineEditWidget(method, attributes, initValue);
            this.__parameterManager = new IndicoUtil.parameterManager();
        });


//Widget to change the number of answers (radio buttons) in abstract reviewing
type("NumberAnswersEditWidget", ["InlineEditWidget"],
        {
            /* builds the basic structure for both display and
               edit modes */
            __buildStructure: function(num) {
                // keep everything in separate lines
                 return Html.table({className:'editLinkInLine'},
                         Html.tbody({},
                                 Html.tr({},
                                         Html.td("dataCaptionFormat", "Number of answers per question :"),
                                         Html.td({}, num))));
                                 },

            _handleEditMode: function(value) {
                // create the fields
                this.num = Html.edit({size: 2}, value);
                // add the fields to the parameter manager
                //this.__parameterManager.add(this.num, 'unsigned_int', false);
                this.__parameterManager.add(this.num, 'unsigned_int', false, function(value){

                    if (value > 20 || value < 2) {
                        return Html.span({}, "Number must be in a range between 2 and 20");
                    } else {
                        return null;
                    }
                });

                // call buildStructure with modification widgets
                return this.__buildStructure(this.num);
            },

            _handleDisplayMode: function(value) {
                // call buildStructure with spans
                return this.__buildStructure(value);
            },

            _getNewValue: function() {
                return this.num.get();
            },

            _verifyInput: function() {
                return this.__parameterManager.check();
            },

            _handleSuccess: function() {
                // previewQuestion is a global var used in ConfModifAbstractRev
                previewQuestion.draw();
            }
        },

        function(method, attributes, initValue) {
            this.InlineEditWidget(method, attributes, initValue, true);
            this.__parameterManager = new IndicoUtil.parameterManager();
        });


//Widget to show an example of question in abstract reviewing
type("ExampleQuestionWidget", ["InlineWidget"],
        {
            draw: function() {

                var self = this;
                // Request to get the new values of number of answers and labels
                indicoRequest(this.method, this.attributes,
                        function(result, error) {
                            if (!error) {
                                var numberAnswers = result.numberAnswers;
                                var labels = result.labels;
                                var rbValues = result.rbValues;
                                var content = Html.div({className:'questionPreview'});
                                content.append(Html.span(null,question));
                                content.append(Html.br());
                                var rbuttons = new RadioButtonSimpleField(null, numberAnswers, labels, rbValues);
                                content.append(rbuttons.draw());

                                $E(self.divId).set(content);

                                rbuttons.addRBTitles();
                            } else {
                                IndicoUtil.errorReport(error);
                            }
                        });
                 }
        },

        function(method, attributes, divId) {
            this.method = method;
            this.attributes = attributes;
            this.InlineWidget();
            this.divId = divId;
        });


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
type("RadioButtonSimpleField", ["ErrorAware"],
        {
            _checkErrorState: function() {
                var checked = false;
                each(this.radioButtons, function(radio) {
                    if(radio.get()) {
                        checked = true;
                    }
                });
                return !checked;
            },

            _setErrorState: function(text) {
                // do nothing. field error display doesn't work well with radio buttons and labels
            },

            get: function() {
                // dummy so ParameterManager doesn't break
            },

            draw: function() {

                this.groupName = Html.generateId(); // The common name for all the radio buttons

                var radioButtons = []; // List of radio buttons

                for (var i=0; i<this.options.length; i++) {
                    // For every option we create a radio button
                    var rb = Html.radio({
                        name: this.name,
                        id: this.groupName + "_" + i,
                        className: "radioButtonAnswer"
                    });
                    rb.dom.value = this.options[i]; //For some reason we have to set the value like this and not in the constructor for it to work in IE
                    radioButtons.push(rb);
                }

                Logic.onlyOne(radioButtons, false); //Ensures that only 1 radio button will be selected at a given time

                if (this.initialValue) {
                    for (var j=0; j<this.options.length; j++) {
                        // We mark as checked the radio button corresponding to 'initialValue' if there is one
                        if (this.options[j] == this.initialValue) {
                            radioButtons[j].dom.defaultChecked = true; //defaultChecked instead of checked seems to do the trick for IE7
                        }
                    }
                }

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
                        htmlFor: this.groupName + "_" + l
                    }, this.labels[l]));
                    row1.append(cell1);

                    var cell2 = Html.td();
                    cell2.append(radioButtons[l]);
                    row2.append(cell2);
                }

                var cellMessage = Html.td();
                cellMessage.dom.style.verticalAlign = "middle";
                cellMessage.dom.rowSpan = 2;

                tbody.append(row1);
                tbody.append(row2);

                if (this.element) {
                    this.element.set(table);
                }

                this.radioButtons = radioButtons;

                return table;
            },

            addRBTitles: function() {
                var self = this;
                // Add the titles for the radio buttons
                for (var i=0; i<this.radioButtons.length; i++) {
                    $E(this.radioButtons[i].dom.id).dom.onmouseover = function(event) {
                        var value = self.rbValues[this.defaultValue];
                        IndicoUI.Widgets.Generic.tooltip(this, event, "<span style='padding:3px'>"+value+"</span>");
                    };
                }
            }
        },

        function(element, options, labels, rbValues, name, initialValue, handler) {
            this.element = element;
            this.options = options;
            this.labels = labels;
            this.initialValue = initialValue;
            this.handler = handler;
            this.rbValues = rbValues;
            this.name = name;
        });


/* Widget to add, remove, edit and show question in the abstract reviewing
@param methods: get, add, remove, edit
@param kindOfElement: Title of the element that you want to manage. Example 'question'
@param specialRemove: Shows if is necessary a special way to remove items
@param divsIdRoot: The main part of the ids of the Footer and ListOfElements ids. (ex. myIdFooter, myIdElements)
@return result (return of request): list of items with the fields 'text': content of the item, 'id': element id.
@return the content of the component. Table with list of elements and input and button to add new elements to the list
*/
type("ManageListOfElements", [],
        {
            draw: function() {
                // Draw the component
                this.widgetContent = Html.div();
                this._buildStructure(this.methods.get, this.attributes);
                return this.widgetContent;
            },

            _buildStructure: function(method, attributes) {

                var self = this;

                indicoRequest(method,
                        attributes,
                        function(result, error){
                            if (!error) {
                                self.widgetContent.append(self._drawListOfElements(result));
                                self.widgetContent.append(self._drawFooter());
                            }
                        });
            },

            _createConfirmPopup: function(method, spanId, previousText, popupContent, title, buttonText) {

                var self = this;

                return new ConfirmPopup(title, popupContent,
                        function(action) {
                            if (action) {
                                var attr = self.attributes;
                                attr['id'] = spanId;
                                if (previousText) {
                                    attr['text'] = popupContent.dom.value;
                                }
                                self._buildStructure(method, attr);
                            }
                        }, buttonText);
            },

            _createSpecialRemovePopup: function(method, spanId, popupContent, title, button1, button2) {

                var self = this;

                return new SpecialRemovePopup(title, popupContent,
                        function(option) {
                            if (option != 0) { // == 0 means close popup
                                var attr = self.attributes;
                                attr['id'] = spanId;

                                if (option == 1) {
                                    // Keep ratings handler
                                    attr['keepJud'] = true;
                                }
                                if (option == 2) {
                                    // Remove ratings handler
                                    attr['keepJud'] = false;
                                }
                                self._buildStructure(method, attr);
                            }
                        }, button1, button2);
            },


            _drawListOfElements: function(result) {
                // Initialize the i counter
                this.i = 0;
                var self = this;

                // Remove previous elements
                if ($E(this.divsIdRoot+'Elements')) {
                    this.widgetContent.remove($E(this.divsIdRoot+'Elements'));
                }

                if (result.length) {
                    var content = Html.div({id:this.divsIdRoot+'Elements'});
                    var table = Html.table({className:'infoQuestionsTable', cellpadding:0, cellPadding:0, cellspacing:0, cellSpacing:0});
                    var tbody = Html.tbody({});
                    table.append(tbody);
                    content.append(table);

                    // Create the table with the required data
                    var tr;
                    var spanRemoveList = [];
                    var spanEditList = [];
                    var tdEdit;
                    var tdRemove;

                    for (var i=0; i < result.length; i++) {
                        tr = Html.tr({className: 'infoTR'});
                        var tdElement = Html.td({className: 'questionContent'}, result[i].text);
                        tdElement.dom.id = "TEID_"+this.divsIdRoot+"_"+result[i].id;

                        // 'Edit' elements and functionality
                        tdEdit = Html.td({className: 'content'});
                        var spanEdit = Html.span({className: 'link'},'Edit');
                        spanEdit.dom.id = "QEID_"+this.divsIdRoot+"_"+result[i].id; // Set the span id with the question id included
                        spanEdit.dom.name = result[i].text;
                        spanEditList.push(spanEdit);
                        tdEdit.append(spanEdit);

                        spanEditList[i].observeClick(function(event) {
                            if (event.target) { // Firefox
                                var spanId = event.target.id.split('_')[2];
                            } else { // IE
                                var spanId = event.srcElement.id.split('_')[2];
                            }
                            var previousText = $E('TEID_'+self.divsIdRoot+"_"+spanId).dom.innerHTML;
                            var popupContent = Html.textarea({id:'modifyArea', cols:'40', rows:'7'}, previousText);
                            var popup = self._createConfirmPopup(self.methods.edit, spanId, previousText, popupContent, 'Edit '+self.kindOfElement, 'Save');
                            popup.open();
                        });

                        // 'Remove' elements and functionality
                        tdRemove = Html.td({className: 'content'});
                        var spanRemove = Html.span({className: 'link'},'Remove');
                        spanRemove.dom.id = "QRID_"+this.divsIdRoot+"_"+result[i].id; // Set the span id with the question id included
                        spanRemoveList.push(spanRemove);
                        tdRemove.append(spanRemove);

                        spanRemoveList[i].observeClick(function(event){
                            if (event.target) { // Firefox
                                var spanId = event.target.id.split('_')[2];
                            } else { // IE
                                var spanId = event.srcElement.id.split('_')[2];
                            }
                            var attr = self.attributes;
                            attr['value'] = spanId;

                            if (!self.specialRemove) {
                                var popupContent = Html.span({}, 'Are you sure you want to remove the '+ self.kindOfElement +'?');
                                var popup = self._createConfirmPopup(self.methods.remove, spanId, null, popupContent, 'Remove '+self.kindOfElement, 'Remove');

                            } else {
                                var popupContent = Html.span({}, 'Do you want to keep the ratings of the judgements for this question (if any)?');
                                // For this popup we need two handlers
                                var popup = self._createSpecialRemovePopup(self.methods.remove, spanId, popupContent, 'Remove '+ self.kindOfElement ,'Keep ratings', 'Remove ratings');
                            }
                            popup.open();
                        });

                        tbody.append(tr);
                        tr.append(tdElement);
                        tr.append(tdEdit);
                        tr.append(tdRemove);
                    }
                }
                return content;
            },

            _drawFooter: function() {

                var self = this;
                // Remove previous elements
                if ($E(this.divsIdRoot+'Footer')) {
                    this.widgetContent.remove($E(this.divsIdRoot+'Footer'));
                }

                var content = Html.div({id: this.divsIdRoot+'Footer', style:{paddingTop:'10px'}});

                var edit = Html.edit({size: '30'});
                var addButton = Html.input('button','popUpButton',$T('Add ' + this.kindOfElement));

                addButton.observeClick(function(){
                      var element = edit.get();
                      if (element != '') {
                          var attr = self.attributes;
                          attr['value'] = element;
                          self._buildStructure(self.methods.add, attr);
                          edit.set('');
                     }
                });

                content.append(edit);
                content.append(addButton);

                return content;
            }

        },

        function(methods, attributes, kindOfElement, divsIdRoot, specialRemove) {
            this.methods = methods;
            this.attributes = attributes;
            this.kindOfElement = kindOfElement;
            this.divsIdRoot = divsIdRoot;
            this.specialRemove = specialRemove;
        });



/* Class manager to show questions in the abstract reviewing
@param divId: Identifier of the div destination
@param numQuestions: number of questions
@param reviewingQuestions: questions dictionary
@param range: range for the number of radio buttons
@param labels: labels shown over between the question and the radio buttons to inform the user of the first and last possible values
@param numAnswers: number of radio buttons (possible answers)
@param rbValues: titles for each radio button
@return none. the div is built inside the showQuestions method
*/
type("QuestionsManager", [],
        {
            showQuestions: function() {

                var newDiv;

                $E(divId).set('');
                for (var i=0; i<this.numQuestions; i++) {
                    newDiv = Html.div({style:{marginLeft:'10px'}});
                    newDiv.append(Html.span(null, this.reviewingQuestions[i].text));
                    newDiv.append(Html.br());

                    var name = 'RB_' + (i+1); // Name of the rb component

                    var rbsf = new RadioButtonSimpleField(null, this.range, this.labels, this.rbValues, name);
                    rbsf.plugParameterManager(this.questionPM);
                    newDiv.append(rbsf.draw());

                    $E(divId).append(newDiv);
                    $E(divId).append(Html.br());
                    rbsf.addRBTitles();
                }
            },

            checkQuestionsAnswered: function() {
                if(this.questionPM.check()) {
                    return true;
                }
                new AlertPopup($T("Warning"), $T("Please answer all questions.")).open();
                return false;
            }
        },

        function(divId, numQuestions, reviewingQuestions, range, labels, numAnswers, rbValues) {
            this.divId = divId;
            this.numQuestions = numQuestions;
            this.reviewingQuestions = reviewingQuestions;
            this.range = range;
            this.labels = labels;
            this.numAnswers = numAnswers;
            this.rbValues = rbValues;
            this.questionPM = new IndicoUtil.parameterManager();
        });
