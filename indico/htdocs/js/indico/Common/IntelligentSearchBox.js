type('IntelligentSearchBox', ['RealtimeTextBox'],
     {
         _highlight: function(elem, token) {
             // Code for highlighting the matched part of the string
             var idx = elem.toLowerCase().indexOf(token.toLowerCase());
             if (idx >= 0) {
                 var before = elem.slice(0, idx);
                 var after = elem.slice(idx+token.length, elem.length);
                 return [before, Html.span("searchSuggestionHighlight", elem.slice(idx,idx+token.length)), after];

             }
         },

         _truncateList: function(list) {

             // truncate the category path, if it is too long

             var first = list.slice(0,1);
             var last = list.length>1?list.slice(-1):[];
             list = list.slice(1,-1);

             var truncated = false;

             var chars = list.join('');
             while(chars.length > 10) {
                 truncated = true;
                 list = list.slice(1);
                 chars = list.join('');
             }

             if (truncated) {
                 list = concat(['...'], list);
             }

             return translate(concat(first,list,last),
                        function(val) {
                            return escapeHTML(val);
                        });
         },

         _truncateTitle: function(title) {
             var max = 27;
             if (title.length > max) {

                 return title.slice(0,max/2) + ' ... ' +
                     title.slice(-max/2);

             } else {
                 return title;
             }
         },

         _showSuggestions: function(text, suggList, totalNumber) {

             var self= this;

             if (!this.suggestionBox) {
                 // Create the suggestion box only once

                 // totalNumber will change during time
                 this.totalNumber = new WatchValue(totalNumber);
                 this.suggestionList = Html.ul('suggestionBoxList');

                 var infoBox = Html.div('searchSuggestionHelpBox',
                     $T("Some category suggestions..."));

                 // Create the suggestion box
                 this.suggestionBox = Html.div({ style: {position: 'absolute',
                                                         top: pixels(23),
                                                         left: 0
                                                        },
                                                 className: 'suggestionBox'},
                                               infoBox,
                                               this.suggestionList,
                                               $B(Html.div("searchSuggestionOtherResults"), this.totalNumber, function(number) {return number===0?'':number + ' ' + $T('other results - please write more...'); })
                                              );

                 this.container.append(this.suggestionBox);
             }

             // Prepare regular expression for highlighting
             var tokens = filter(escapeHTML(text).split(' '), function(t) { return t !== '';});
             var tokenRE = new RegExp("("+tokens.join('|')+")", 'gi');


             // Bind the list to the DOM element

             var counter = 0;

             $B(this.suggestionList, suggList,
                function(elem) {
                    var titleHtml = escapeHTML(self._truncateTitle(elem.title)).replace(tokenRE, '<span class="searchSuggestionHighlight">$1</span>');

                    var index = counter;

                    var title = Html.span('searchSuggestionTitle');
                    title.dom.innerHTML = titleHtml;
                    var pathText = self._truncateList(elem.path).join(' >> ');
                    var path = Html.div('searchSuggestionPath', pathText);
                    var liItem = Html.li({}, title, path);

                    // Use mouse to control selector as well

                    liItem.observeEvent('mouseover', function() {
                        if (self.selectorPos != index) {
                            self._clearSelector();
                            self.selectorPos = index;
                            self._setSelector();
                        }
                    });

                    liItem.observeClick(function() {
                        window.location = elem.url;
                    });


                    counter++;

                    return liItem;
                });

             this.suggestionList.observeEvent('mouseout', function() {
                 self._clearSelector();
                 self.selectorPos = -1;
             });


             // Update
             this.totalNumber.set(totalNumber);
         },

         _hideSuggestions: function() {
             this.container.remove(this.suggestionBox);
             this.suggestionBox = null;
             this.selectorPos = -1;
             this.suggestions = null;
         },

         _retrieveOptions: function(expression) {
             this.querying = true;
             var self = this;
             indicoRequest('search.categoryName',
                           {value: expression},
                           function(result, error) {
                               self.querying = false;
                               if (!error) {
                                   if (result.list.length > 0) {
                                       self.suggestions = result.list;
                                       self._showSuggestions(expression, result.list, result.number - result.list.length);
                                   } else {
                                       self._hideSuggestions();
                                   }

                                   currentText = trim(self.get());

                                   // if the text changed meanwhile and it
                                   // is still long enough
                                   if (currentText != expression &&
                                       currentText.length > 1) {
                                       // request
                                       self._retrieveOptions(currentText);
                                   } else if (currentText.length <= 1){
                                       // if it is not long enough
                                       self._hideSuggestions();
                                   }
                               } else {
                                   IndicoUtil.errorReport(error);
                               }

                           });
         },

         /*
          * Called each time a new character is typed
          * strips white spaces, and calls for a request if needed
          */
         _textTyped: function(key) {

             var text = trim(this.get());

             if(text.length > 1) {
                 if(!this.querying) {
                     this._retrieveOptions(text);
                 }
             } else if (this.suggestionBox) {
                 this._hideSuggestions();
             }
         },

         _openSelection: function(event) {
             if (this.selectorPos >= 0) {
                 window.location = this.suggestions[this.selectorPos].url;
                 return false;
             }
             return true;
         },

         /*
          * Move the selector (gray area) up or down
          */
         _moveSelector: function(direction) {

             if (this.suggestionBox) {
                 var suggNum = this.suggestionList.length.get();

                 if(this.selectorPos < 0) {
                     this.selectorPos = direction=='down'?0:suggNum-1;
                 } else {
                     this._clearSelector();
                     this.selectorPos += direction=='up'?-1:1;

                     if (this.selectorPos >= suggNum) {
                         this.selectorPos = -1;
                     } else if (this.selectorPos < 0) {
                         this.selectorPos = -1;
                     }
                 }
             }

             this._setSelector();
         },

         _setSelector: function() {
             if (this.selectorPos >= 0) {
                 this.suggestionList.item(this.selectorPos).dom.className = 'searchSuggestionSelected';
             }
         },

         _clearSelector: function() {
             if (this.selectorPos >= 0) {
                 this.suggestionList.item(this.selectorPos).dom.className = '';
             }
         }

     },
     function(args, container, submitBtn){
         args.autocomplete = 'off';
         this.RealtimeTextBox(args);
         this.selectorPos = -1;
         this.querying = false;
         this.container = container;

         var self = this;

         this.observe(function(key, event) {
             self._textTyped(key);
             return true;
         });

         this.observeOtherKeys(function(text, key, event) {
             if (key == 38 || key == 40) {
                 self._moveSelector(key==38?'up':'down');
                 return false;
             } else if (key == 27) {
                 self._hideSuggestions();
                 return false;
             } else if (key == 13) {
                 return self._openSelection(event);
             } else {
                 return true;
             }
         });

         $E(document.body).observeClick(function(event) {
             // Close box if a click is done outside of it

             /* for some unknown reason, onclick is called on the submit button,
              * as soon as the return key is pressed in any of the textfields.
              * To make it even better, onclick is called before onkeyup,
              * which forces us to do the last two checks.
              */

             if (self.suggestionBox &&
                 !self.suggestionList.ancestorOf($E(eventTarget(event))) &&
                 $E(eventTarget(event)) != self.input &&
                 $E(eventTarget(event)) != submitBtn)
             {
                 self._hideSuggestions();
             }
         });

     }
    );
