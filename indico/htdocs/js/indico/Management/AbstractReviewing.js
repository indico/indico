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
