
//Widget to change the scale in abstract reviewing
type("ScaleEditWidget", ["InlineEditWidget"],
        {
            /* builds the basic structure for both display and
               edit modes */

            __buildStructure: function(minValue, maxValue, warning) {

                var div = Html.div({style:{paddingLeft:'2px'}});
                var spanTitle = Html.span({className:'dataCaptionFormat'},"Scale for each answer: ")
                var structure = Html.table({},
                                    Html.tbody({},
                                        Html.tr({},Html.td("supportEntry", "From :"),
                                            Html.td({}, minValue)),
                                        Html.tr({},Html.td("supportEntry", "To :"),
                                            Html.td({}, maxValue))));
                div.append(spanTitle);
                div.append(structure)
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
                    alert("The \"From\" value must be lower than \"To\" value.");
                    return false;
                } else if ((parseInt(this.max.dom.value) - parseInt(this.min.dom.value)) > 100) {
                    alert("The maximun difference between limits is 100 units.");
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
                        var error = Html.span({}, "Number must be in a range between 2 and 20");
                        return error;
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
                if (!this.__parameterManager.check()) {
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


//Widget to show an example of question in abstract reviewing
type("ExampleQuestionWidget", ["InlineWidget"],
        {
            draw: function() {
                this.numReq += 1;
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
                                content.append(new RadioButtonPreviewQuestion(
                                        numberAnswers,
                                        labels,
                                        self.numReq).draw());
                                $E('inPlaceShowExample').set(content);
                                for (var j=0; j<numberAnswers.length; j++) {
                                    $E("_GID"+self.numReq+"_" + j).dom.onmouseover = function(event) {
                                        var value = rbValues[this.defaultValue];
                                        IndicoUI.Widgets.Generic.tooltip(this, event, "<span style='padding:3px'>"+value+"</span>");
                                    };
                                }
                            } else {
                                IndicoUtil.errorReport(error);
                            }
                        });
                 }
        },

        function(method, attributes) {
            this.method = method;
            this.attributes = attributes;
            this.numReq = 0;
            this.InlineWidget();
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
type("RadioButtonSimpleField", [],
        {
            draw: function() {

                var groupName = Html.generateId(); // The common name for all the radio buttons

                var radioButtons = []; // List of radio buttons

                for (var i=0; i<this.options.length; i++) {
                    // For every option we create a radio button
                    var rb = Html.radio({
                        name: groupName,
                        id: groupName + "_" + i,
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
                        htmlFor: groupName + "_" + l
                    }, this.labels[l]));
                    row1.append(cell1);

                    var cell2 = Html.td();
                    cell2.append(radioButtons[l]);
                    row2.append(cell2);
                }

                cellMessage = Html.td();
                cellMessage.dom.style.verticalAlign = "middle";
                cellMessage.dom.rowSpan = 2;

                tbody.append(row1);
                tbody.append(row2);

                if (this.element) {
                    this.element.set(table);
                }

                return table;
            }
        },

        function(element, options, labels, initialValue, handler) {
            this.element = element;
            this.options = options;
            this.labels = labels;
            this.initialValue = initialValue;
            this.handler = handler;
        });


type("RadioButtonPreviewQuestion", [],
        {
            draw: function() {

                var groupName = "_GID"+this.numId; // The common name for all the radio buttons

                var radioButtons = []; // List of radio buttons

                for (var i=0; i<this.options.length; i++) {
                    // For every option we create a radio button
                    var rb = Html.radio({
                        name: groupName,
                        id: groupName + "_" + i,
                        className: "radioButtonAnswer"
                    });
                    rb.dom.value = this.options[i]; //For some reason we have to set the value like this and not in the constructor for it to work in IE
                    radioButtons.push(rb);
                }

                Logic.onlyOne(radioButtons, false); //Ensures that only 1 radio button will be selected at a given time

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
                    }, this.labels[l]));
                    row1.append(cell1);

                    var cell2 = Html.td();
                    cell2.append(radioButtons[l]);
                    row2.append(cell2);
                }

                cellMessage = Html.td();
                cellMessage.dom.style.verticalAlign = "middle";
                cellMessage.dom.rowSpan = 2;

                tbody.append(row1);
                tbody.append(row2);

                return table;
            }
        },

        function(options, labels, numId) {
            this.options = options;
            this.labels = labels;
            this.numId = numId;
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

                var self = this;
                this.widgetContent = Html.div();

                indicoRequest(this.methods.get,
                        this.attributes,
                        function(result, error){
                            if (!error) {
                                self.widgetContent.append(self._drawListOfElements(result));
                                self.widgetContent.append(self._drawFooter());
                            }
                        });

                return this.widgetContent
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
                        tdElement = Html.td({className: 'questionContent'}, result[i].text);
                        tdElement.dom.id = "TEID_"+result[i].id;

                        // 'Edit' elements and functionality
                        tdEdit = Html.td({className: 'content'});
                        var spanEdit = Html.span({className: 'link'},'Edit');
                        spanEdit.dom.id = "QEID_"+result[i].id; // Set the span id with the question id included
                        spanEdit.dom.name = result[i].text;
                        spanEditList.push(spanEdit);
                        tdEdit.append(spanEdit);

                        spanEditList[i].observeClick(function(event) {
                            if (event.target) { // Firefox
                                var spanId = event.target.id.split('_')[1];
                            } else { // IE
                                var spanId = event.srcElement.id.split('_')[1];
                            }
                            var previousText = $E('TEID_'+spanId).dom.innerHTML;
                            var popupContent = Html.textarea({id:'modifyArea', cols:'40', rows:'7'}, previousText);
                            var popup = new ConfirmPopup('Edit '+this.kindOfElement, popupContent,
                                    function(action) {
                                        if (action) {
                                            var attr = self.attributes;
                                            attr['id'] = spanId;
                                            attr['text'] = popupContent.dom.value;
                                            indicoRequest(self.methods.edit,
                                                attr,
                                                function(result, error){
                                                   if (!error) {
                                                       self.widgetContent.append(self._drawListOfElements(result));
                                                       self.widgetContent.append(self._drawFooter());
                                                    }
                                                 });
                                            }
                                    }, 'Save');
                            popup.open();
                        });

                        // 'Remove' elements and functionality
                        tdRemove = Html.td({className: 'content'});
                        var spanRemove = Html.span({className: 'link'},'Remove');
                        spanRemove.dom.id = "QRID_"+result[i].id; // Set the span id with the question id included
                        spanRemoveList.push(spanRemove);
                        tdRemove.append(spanRemove);

                        spanRemoveList[i].observeClick(function(event){
                            if (event.target) { // Firefox
                                var spanId = event.target.id.split('_')[1];
                            } else { // IE
                                var spanId = event.srcElement.id.split('_')[1];
                            }
                            var attr = self.attributes;
                            attr['value'] = spanId;
                            if (!self.specialRemove) {
                                var popupContent = Html.span({}, 'Are you sure you want to remove the '+ self.kindOfElement +'?');
                                var popup = new ConfirmPopup('Remove '+ self.kindOfElement, popupContent,
                                         function(action) {
                                             if (action) {
                                                 var attr = self.attributes;
                                                 attr['id'] = spanId;
                                                 indicoRequest(self.methods.remove,
                                                         attr,
                                                         function(result, error){
                                                             if (!error) {
                                                                self.widgetContent.append(self._drawListOfElements(result));
                                                                self.widgetContent.append(self._drawFooter());
                                                             }
                                                  });
                                            }
                                        }, 'Remove');
                            } else {
                                var popupContent = Html.span({}, 'Do you want to keep the ratings of the judgements for this question (if any)?');
                                // For this popup we need two handlers
                                var popup = new SpecialRemovePopup('Remove '+ self.kindOfElement, popupContent,
                                    function(option) {
                                            if (option == 0) {
                                                // close popup option
                                                null;
                                            }
                                            if (option == 1) {
                                                // Keep ratings handler
                                                var attr = self.attributes;
                                                attr['id'] = spanId;
                                                attr['keepJud'] = true;
                                                indicoRequest(self.methods.remove,
                                                    attr,
                                                    function(result, error){
                                                        if (!error) {
                                                            self.widgetContent.append(self._drawListOfElements(result));
                                                            self.widgetContent.append(self._drawFooter());
                                                            }
                                                     });
                                            }
                                            if (option == 2) {
                                                // Remove ratings handler
                                                var attr = self.attributes;
                                                attr['id'] = spanId;
                                                attr['keepJud'] = false;
                                                indicoRequest(self.methods.remove,
                                                    attr,
                                                    function(result, error){
                                                        if (!error) {
                                                            self.widgetContent.append(self._drawListOfElements(result));
                                                            self.widgetContent.append(self._drawFooter());
                                                            }
                                                    });
                                            }
                                        }, 'Keep ratings', 'Remove ratings');
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
                          indicoRequest(self.methods.add,
                                  attr,
                                  function(result, error){
                                      if (!error) {
                                          self.widgetContent.append(self._drawListOfElements(result));
                                          self.widgetContent.append(self._drawFooter());
                                      }
                                  });
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
