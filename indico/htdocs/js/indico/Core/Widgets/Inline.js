
type("InlineWidget", ["IWidget"],
     {
         _error: function(error) {
             IndicoUI.Dialogs.Util.error(error);
         }
     });


/*
 * This class implements a widget that interacts directly with the
 * remote server. States are handled, through a callback interface.
 */
type("InlineRemoteWidget", ["InlineWidget"],

     {

         _handleError: function(error) {
             this._error(error);
         },

         _handleLoading: function(error) {
             return Html.span({}, 'loading...');
         },

         _handleLoaded: function() {
             // do nothing, overload
         },

         _handleSuccess: function() {
             // do nothing, overload
         },

         _handleBackToEditMode: function() {
             // do nothing, overload
         },

         draw: function() {
             var self = this;

             var content = this._handleContent();

             // if the widget is set to load on startup,
             // the content will be a 'loading' message
             this.wcanvas = Html.div({}, this.loadOnStartup?
                                   this._handleLoading():
                                   content);

             // observe state changes and call
             // the handlers accordingly
             this.source.state.observe(function(state) {
                 if (state == SourceState.Error) {
                     self._handleError(self.source.error.get());
                     self.wcanvas.set(content);
                     self.setMode('edit');
                     self._handleBackToEditMode();
                 } else if (state == SourceState.Loaded) {
                     self._handleLoaded(self.source.get());
                     self.wcanvas.set(content);
                     self.setMode('display');
                     self._handleSuccess();
                 } else {
                     self.wcanvas.set(self._handleLoading());
                 }
             });

             return self.wcanvas;
         }

     },
     /*
      * method - remote method
      * attributes - attributes that are passed
      * loadOnStartup - should the widget start loading from the
      * server automatically?
      */
     function(method, attributes, loadOnStartup, callback) {
         loadOnStartup = exists(loadOnStartup)?loadOnStartup:true;
         this.ready = new WatchValue();
         this.ready.set(false);
         this.loadOnStartup = loadOnStartup;
         this.source = indicoSource(method, attributes, null, !loadOnStartup, callback);
     });

type("InlineRemoteWidgetForOptionButton", ["InlineWidget"],
     {
         draw: function() {
             var self = this;
             var canvas = Html.span({}, 'loading...');
             canvas.set(self.drawContent());
             var message = Html.span({style: {marginLeft:'10px'}},'\u00A0');
             message.dom.id = this.messageId;

             var table = Html.table();
             var tbody = Html.tbody();
             var row1 = Html.tr();
             var cell2 = Html.td();

             table.dom.style.display = 'inline';
             table.set(tbody);

             cell2.append(canvas);
             row1.append(cell2);

             cellMessage = Html.td();
             cellMessage.dom.style.verticalAlign = "middle";
             cellMessage.dom.rowSpan = 2;
             cellMessage.append(message);
             row1.append(cellMessage);

             tbody.append(row1);

             this.source.state.observe(function(state) {
                 var to = 0;
                 if (state == SourceState.Error) {
                     self.ready.set(true);
                     self._error(self.source.error.get());
                 } else if (state == SourceState.Committing) {
                     self.ready.set(true);
                     message.set('Saved');
                     message.dom.style.color='green';
                     to = setTimeout("$E(\""+self.messageId + "\").set(\'\u00A0\')", 2000);
                 } else if (state == SourceState.Loaded) {
                     clearTimeout(to);
                 } else {
                     message.set(' ');
                 }
             });

             return table;
         }

     },
     function(method, attributes) {
         this.ready = new WatchValue();
         this.ready.set(false);
         this.source = indicoSource(method, attributes);
     });

type("SwitchOptionButton", ["InlineRemoteWidgetForOptionButton"],
     {
         error: function(error) {
             this.checkbox.set(true);
             alert(error.message);
         },

         drawContent: function() {
             return Html.div({},
                             this.checkbox,
                             this.caption);

         }
     },
     function(method, attributes, caption, messageId) {
         this.InlineRemoteWidgetForOptionButton(method, attributes);
         this.caption = caption;
         this.checkbox = Html.checkbox({});
         this.messageId = messageId;

         $B(this.checkbox, this.source);
     });


/*
 * This switch button is a 2-state switch that allows different requests to be
 * performed depending on whether the button should be enabled or disabled
 */
type("RemoteSwitchButton", ["InlineWidget"],
     {
         draw: function() {

             // icon for "in progress" state
             var imageLoading = Html.img({
                 src: imageSrc("loading"),
                 alt: 'Loading',
                 title: $T('Communicating with server')
             });

             var self = this;

             var request = function(currentState, targetState, method) {
                 indicoRequest(method,
                               self.args, function(response, error){
                                   if (exists(error)) {
                                       self._error(error);
                                       chooser.set(currentState);
                                   }
                                   else {
                                       chooser.set(targetState);
                                   }

                               });
             };

             var chooser = new Chooser(
                 { 'disable': command(
                     function(event){
                         chooser.set('progress');
                         // server request to disable the button
                         request('disable','enable',self.enableMethod);
                         stopPropagation(event);
                         return false;
                     }, this.imgEnabled),

                   'enable': command(
                       function(event){
                           chooser.set('progress');
                           // server request to enable the button
                           request('enable','disable',self.disableMethod);
                           stopPropagation(event);
                           return false;
                       }, this.imgDisabled),

                   // "in progress"
                   'progress': command(function() { return false; },
                                       imageLoading)


                 });

             chooser.set(this.initState?'disable':'enable');

             return Widget.link(chooser);
         }
     },
     /*
      * initState - initial state (true=enabled, false=disabled)
      * imgEnabled - image for 'enabled' state
      * imgDisabled - image for 'disabled' state
      * enableMethod - remote method to be called in order to pass to "enabled state"
      * disableMethod - remote method to be called in order to pass to "disabled state"
      * args - extra args to be passed to either method
      */
     function(initState, imgEnabled, imgDisabled, enableMethod, disableMethod, args) {
         this.initState = initState;
         this.imgEnabled = imgEnabled;
         this.imgDisabled = imgDisabled;
         this.enableMethod = enableMethod;
         this.disableMethod = disableMethod;
         this.args = args;
     });



type("RadioFieldWidget", ["InlineWidget", "WatchAccessor"],
     {
         draw: function() {
             var self = this;

             this.canvas = Html.div(
                 {style:{position:'relative'}},
                 Html.table(this.cssClassRadios,
                 $B(Html.tbody({}),
                     this.orderedItems,
                     function(item) {
                         var radio = self.radioDict[item.key];
                         radio.observeClick(function() {
                             self.select(item.key);
                         });
                         self.options.accessor(item.key).observe(
                             function(value) {
                                 radio.set(value);
                                 if (value) {
                                     liItem.dom.className = 'selectedItem';
                                 } else {
                                     liItem.dom.className = '';
                                 }
                             });

                         var itemContent = item.get();

                         if (itemContent.IWidget) {
                             itemContent = itemContent.draw();
                         } else {
                             itemContent = Html.span({style:{verticalAlign: 'middle'}}, itemContent);
                         }

                         // create li item, add visibility info too
                         var liItem = Html.tr(
                             self.visibility.get(item.key) ? {} : 'disabledRadio',
                             keys(self.radioDict).length > 1 ? Html.td({}, radio):'',
                             Html.td( {}, itemContent ));
                         radio.dom.disabled = !self.visibility.get(item.key);

                         if (self.options.get(item.key)) {
                             liItem.dom.className = 'selectedItem';
                         }


                         // observe future changes in visibility
                         self.visibility.accessor(item.key).observe(
                             function(value) {
                                 if (!value) {
                                     liItem.dom.className = 'disabledRadio';
                                     radio.dom.disabled = true;
                                 } else {
                                     liItem.dom.className = 'enabledRadio';
                                     radio.dom.disabled = false;
                                 }
                                 if (!value && radio.get()) {
                                     self.selectLast();
                                 }
                             });


                         return liItem;
                     })));

             return this.canvas;
         },

         setVisibility: function(key, visible) {
             this.visibility.set(key, visible);
         },

         show: function() {
             this.canvas.dom.style.display =  'block';
         },

         hide: function() {
             this.canvas.dom.style.display =  'none';
         },

         onSelect: function(state) {
         },

         set: function(state) {
             this.select(state);
         },

         get: function() {
             var selKey = null;

             each(this.options, function(value, key){
                 if (value) {
                     selKey = key;
                 }
             });

             return selKey;
         },


         enable: function() {
             each(this.radioDict,
                  function(value, key) {
                      value.dom.disabled = false;
                  });

             this.canvas.dom.style.opacity = 1;
         },

         disable: function() {
             each(this.radioDict,
                  function(value, key) {
                      value.dom.disabled = true;
                  });

             this.canvas.dom.style.opacity = 0.4;
         },

         observe: function(callback) {
             this.options.observe(function(value, key){
                 if (value) {
                     callback(key);
                 }
             });
         },

         select: function(state, /* optional */ fromSource) {
             /* fromSource specifies whether the source
                structure should be updated according
                to the widgets or not (useful for
                distinguishing initialization)*/

             var self = this;
             var widget = this.items[state];
             if (widget.IWidget) {
                 widget.enable();
             }

             self.state.set(state);
             // set every other option to false
             self.options.each(function(value, key) {

                 if (value) {
                     self.options.set(key, false);
                 }
                 if (key != state) {
                     var widget = self.items[key];
                     if (widget.IWidget) {
                         widget.disable();
                     }
                 }

             });

             self.options.set(state, true);

             // update the DOM element
             self.radioDict[state].set(true);

             // onSelect
             self.onSelect(state, fromSource);
         },

         selectLast: function() {
             var visible = [];
             var self = this;

             // check the visibility of the items,
             // by order, and choose the first one
             // that is visible
             each(this.orderedItems,
                  function(item) {
                      if (self.visibility.get(item.key)) {
                          visible.push(item.key);
                      }
                  });

             if (visible.length > 0) {
                 this.select(visible[visible.length-1]);
             }
         }
     },

     function(items, cssClassRadios) {
         this.items = {};
         this.radioDict = {};
         this.options = new WatchObject();
         this.visibility = new WatchObject();
         this.cssClassRadios = exists(cssClassRadios)?cssClassRadios:'nobulletsList';

         var self = this;


         var name = Html.generateId();

         this.orderedItems = $L();
         each(items,
              function(item) {
                  var key = item[0];
                  self.items[key] = item[1];
                  self.orderedItems.append(new WatchPair(key, item[1]));

                  // add some extra stuff, since we're in the loop
                  self.visibility.set(key, true);
                  self.options.set(key, false);
                  self.radioDict[key] = Html.radio({'name': name,
                                                    style: {verticalAlign: 'middle'}});
              });

         this.state = new Chooser(map(items,
                                      function(value, key) {
                                          return key;
                                      }));


     });

type("SelectRemoteWidget", ["InlineRemoteWidget", "WatchAccessor"],
     {
         _drawItem: function(item) {
             var option = Widget.option(item);// Html.option({value: item.key}, item.get());

             if (this.selected.get()) {
                 if (this.selected.get() == item.key) {
                     option.accessor('selected').set(true);
                 }
             }

             return option;
         },

         _handleContent: function() {
             var self = this;

             return bind.element(this.select,
                                 this.source,
                                 function(item) {
                                     if ($.isArray(item)) {
                                         item = new WatchPair(item[0], item[1]);
                                     }
                                     return self._drawItem(item);
                                 });
         },

         observe: function(func) {
             this.select.observe(func);
         },
         refresh: function() {
             this.source.refresh();
         },
         disable: function() {
             this.select.dom.disabled = true;
         },
         enable: function() {
             this.select.dom.disabled = false;
         },
         get: function() {
             return this.select.get();
         },
         set: function(option) {
             this.selected.set(option);
         },
         unbind: function() {
             bind.detach(this.select);
         }

     },
     function(method, args, callback) {
         this.select = Html.select({});
         this.selected = new WatchValue();
         // Load data source on startup
         this.InlineRemoteWidget(method, args, true, callback);
         this.loadOnStartup = false;
     });


type("RealtimeTextBox", ["IWidget", "WatchAccessor", "ErrorAware"],
     {
         _setErrorState: function(text) {
             this._stopErrorList = this._setElementErrorState(this.input, text);
         },

         _checkErrorState: function() {
             return null;
         },

         draw: function() {
             this.enableEvent();
             return this.IWidget.prototype.draw.call(this, this.input);
         },
         get: function() {
             if (this.input.dom.disabled){
                 return null;
             } else {
                 return this.input.get();
             }
         },
         set: function(value) {
             return this.input.set(value);
         },
         observe: function(observer) {
             this.observers.push(observer);
         },
         observeEvent: function(event, observer) {
             return this.input.observeEvent(event, observer);
         },
         observeOtherKeys: function(observer) {
             this.otherKeyObservers.push(observer);
         },
         stopObserving: function() {
             this.observers = [];
             this.otherKeyObservers = [];
         },
         unbind: function() {
             bind.detach(this.input);
         },
         disable: function() {
             this.input.dom.disabled = true;
         },
         enable: function() {
             this.input.dom.disabled = false;
             this.enableEvent();
         },
         setStyle: function(prop, value) {
             this.input.setStyle(prop, value);
         },
         setFocus: function() {
             this.input.dom.focus();
         },
         notifyChange: function(keyCode, event) {
             var value = true;
             var self = this;

             each(this.observers, function(func) {
                 value = value && func(self.get(), keyCode, event);
             });
             return value;
         },
         enableEvent: function() {
             var self = this;

             this.input.observeEvent('keydown', function(event) {
                 var keyCode = event.keyCode;
                 var value = true;

                 if ((keyCode < 32 && keyCode != 8) || (keyCode >= 33 && keyCode < 46) || (keyCode >= 112 && keyCode <= 123)) {
                     each(self.otherKeyObservers, function(func) {
                         value = value && func(self.get(), keyCode, event);
                     });
                     return value;
                 }
                 return true;
             });


             // fire onChange event each time there's a new char
             this.input.observeEvent('keyup', function(event) {
                 var keyCode = event.keyCode;

                 if (!((keyCode < 32 && keyCode != 8) || (keyCode >= 33 && keyCode < 46) || (keyCode >= 112 && keyCode <= 123))) {
                     var value = self.notifyChange(keyCode, event);
                     Dom.Event.dispatch(self.input.dom, 'change');
                     return value;
                 }
                 return true;
             });
         }
     },
     function(args) {
         this.observers = [];
         this.otherKeyObservers = [];
         this.input = Html.input('text', args);
     });

type("RealtimeTextArea", ["RealtimeTextBox"],
     {
     },
     function(args) {

         this.RealtimeTextBox(clone(args));
         this.input = Html.textarea(args);
     });

/**
 * Normal text field which is triggering an action when the user actions the ENTER key.
 */
type("EnterObserverTextBox", ["IWidget", "WatchAccessor"],
        {
            draw: function() {
                return this.IWidget.prototype.draw.call(this, this.input);
            },
            get: function() {
                return this.input.get();
            },
            set: function(value) {
                return this.input.set(value);
            },
            observe: function(observer) {
                this.input.observe(observer);
            },
            getInput: function() {
                return this.input;
            }
        },
        function(id, args, keyPressAction) {
            var self = this;
            this.input = Html.input(id, args);
            // fire event when ENTER key is pressed
            this.input.observeEvent('keypress', function(event) {
                if (event.keyCode == 13) {
                    Dom.Event.dispatch(self.input.dom, 'change');
                    return keyPressAction();
                }
                Dom.Event.dispatch(self.input.dom, 'change');
            });
        });

type("FlexibleSelect", ["IWidget", "WatchAccessor"],
     {

         _decorate: function(key, elem) {
             return this.decorator(key, elem);
         },

         _defaultDecorator: function(key, elem) {
             return Html.li('bottomLine', elem);
         },

         _drawOptions: function() {

             if (!this.optionBox) {
                 // Create the option box only once

                 this.optionList = Html.ul('optionBoxList');

                 var liAdd = Html.span('fakeLink',
                     Html.span({style: {fontStyle: 'italic'}}, $T('Add a different one')));
                 liAdd.href = null;
                 liAdd.observeClick(function() {
                     self._startNew();
                 });

                 this.optionBox = Html.div({ style: {position: 'absolute',
                                                     top: pixels(20),
                                                     left: 0
                                                    },
                                             className: 'optionBox'},
                                           this.optionList,
                                           Html.div('optionBoxAdd', liAdd)
                                          );

                 var self = this;

                 $B(this.optionList,
                    this.list,
                    function(elem) {
                        var li = self._decorate(elem.key, elem.get());

                        li.observeClick(function() {
                            self.set(elem.key);
                            self._hideOptions();
                            return false;
                        });

                        return li;
                    });



                 this.container.append(this.optionBox);
             }
         },

         _observeBlurEvents: function(leaveEditable) {
             var self = this;
             this.stopObservingBlur =
                 this.input.observeEvent('blur',
                                         function() {
                                             self._endNew(self.input.get(), leaveEditable);
                                         });

             this.input.observeOtherKeys(
                 function(text, key, event) {
                     if (key == 13) {
                         self._endNew(text, leaveEditable);
                     }
                 });
         },

         _stopObservingBlurEvents: function()  {
             this.input.stopObserving();
             this.stopObservingBlur();
         },

         _startNew: function() {
             this._hideOptions();
             this.input.enable();
             this.input.setFocus();

             this.input.set('');
             this.value.set('');

             //this._observeBlurEvents();

         },

         _endNew: function(text, leaveEditable) {
             this.value.set(text);

             if (!leaveEditable) {
                 this.input.disable();
                 bind.detach(this.input);
                 bind.detach(this.value);
                 //this._stopObservingBlurEvents();
             }

             this._notify();
         },

         _hideOptions: function() {
             this.container.remove(this.optionBox);
             this.optionBox = null;
         },

         _notify: function() {
             var self = this;
             each(this.observers,
                  function(observer) {
                      observer(self.get());
                  });
         },

         draw: function() {
             var self = this;

             this.trigger.observeClick(function() {
                 if (!self.disabled) {
                     self._drawOptions();
                 }
             });

             this.container = Html.div('flexibleSelect', this.trigger, this.input.draw(), this.notificationField);

             return this.container;
         },

         get: function() {
             return this.value.get();
         },
         set: function(value) {

             var oldVal = this.get();

             if (this.list.get(value)) {
                 this.input.set(this.list.get(value));
             } else {
                 this.input.set(value);
                 this.enableInput();
             }

             this.value.set(value);

             if (oldVal != this.get()) {
                 this._notify();
             }

             return this.get();
         },
         observe: function(observer) {
             this.observers.push(observer);
         },
         invokeObserver: function(observer) {
             return observer(this.get());
         },
         disable: function() {
             this.container.dom.className = 'flexibleSelect disabled';
             this.input.disable();
             this.disabled = true;
         },
         enable: function() {
             this.container.dom.className = 'flexibleSelect';
             this.disabled = false;

             if (!this.inputDisabled) {
                 this.enableInput();
             }
         },
         disableInput: function() {
             this.inputDisabled = true;
             this.input.disable();
         },
         enableInput: function() {
             this.inputDisabled = false;
             this.input.enable();
         },
         setOptionList: function(list) {
             //this.disableInput();
             this.list.clear();
             this.list.update(list);
             this.list.sort(this.sortCriteria);

             var self = this;
             if (keys(list).length === 0) {
                 this.trigger.dom.style.display = 'none';
             }
             if ( !exists(this.list.get(this.value.get()))) {
                 this.enableInput();
                 $B(this.input, this.value);

                 //this._observeBlurEvents(true);

                 // focus() needs some time to get ready (?)
                 //setTimeout(function() {self.input.setFocus();}, 20);
             }
         },
         setLoading: function(state) {
             if (state) {
                 this.trigger.dom.style.display = 'inline';
             }

             this.loading.set(state);
         },

         detach: function() {
             bind.detach(this.value);
             this.input.unbind();
         }


     }, function(list, width, sortCriteria, decorator) {

         width = width || 150;

         this.decorator = decorator || this._defaultDecorator;
         this.sortCriteria =  sortCriteria || SortCriteria.Integer;

         this.value = new WatchValue();
         this.input = new RealtimeTextBox({style:{border: 'none', width: pixels(width)}});
         this.input.disable();
         this.disabled = false;
         this.inputDisabled = true;
         this.loading = new WatchValue();
         this.observers = [];

         this.notificationField = Html.div({style:{color: '#AAAAAA', position:'absolute', top: '0px', left: '5px'}});

         this.list = $D(list);
         this.list.sort(this.sortCriteria);

         var self = this;

         this.trigger = Html.div('arrowExpandIcon');

         $B(this.value, this.input);
         this.value.observe(function(value) {
             self._notify();
         });

         this.loading.observe(function(value) {
             self.trigger.dom.className = value?'progressIcon':'arrowExpandIcon';
         });

         $E(document.body).observeClick(function(event) {
             // Close box if a click is done outside of it

             if (self.optionBox &&
                 !self.optionList.ancestorOf($E(eventTarget(event))) &&
                 eventTarget(event) != self.trigger.dom)
             {
                 self._hideOptions();
             }
         });

         this.WatchAccessor(this.get, this.set, this.observe, this.invokeObserver);

     });

/**
 * This type creates a DIV containing a button which is disabled and
 * it places another DIV over it in order to be able to observe events.
 *
 * It also allows to enable/disable the button and check if it is enabled.
 *
 * @param {Html.input} button The button that will be added to the div.
 *
 */
type("DisabledButton", ["IWidget", "WatchAccessor"],
{
        draw: function() {
            return this.IWidget.prototype.draw.call(this, this.div);
            },

        observeEvent: function(observer, func) {
            this.div.observeEvent(observer, func);
            },

        observeClick: function(func) {
            var self = this;
            this.div.observeClick(function(){
                if (!self.button.dom.disabled) {
                    func();
                }
            });
        },

        enable: function() {
            this.button.dom.disabled = false;
            this.topTransparentDiv.dom.style.display = "none";
        },
        disable: function() {
            this.button.dom.disabled = true;
            this.topTransparentDiv.dom.style.display = "";
        },
        isEnabled: function() {
            return !this.button.dom.disabled;
        }
},
function(button){
    var self = this;
    this.button = button;
    this.topTransparentDiv = Html.div({style:{position:"absolute",top:pixels(0), left:pixels(0), width:Browser.IE?"":"100%", height:Browser.IE?"":"100%"}});
    this.div = Html.div({style:{display:"inline", position:Browser.IE?"":"relative"}},button, this.topTransparentDiv);
}
);

/**
 * This widget displays a text with a (Hide) fakelink next to it.
 * If the (Hide) fakelink is clicked, a message will appear and the (Hide) button will change to (Show)
 * Example of usage: we want to display a password to a user but show it initially hidden
 *
 * @param {String} text The text that we want to optionally show or not.
 * @param {String} hiddenMessage The text to show when "text" is hidden.
 * @param {Boolean} true if we want to show the text initially, false otherwise
 */
type("HiddenText", ["IWidget"], {
    draw: function() {
        var self = this;

        var content = $B(Html.div({style:{display:"inline"}}), this.show, function(show) {
            var message;
            var button;
            if (show) {
                message = self.text;
                button = Html.span("fakeLink", " (" + $T("Hide") + ")");
                button.observeClick(function(){
                    self.show.set(false);
                });
            } else {
                message = self.hiddenMessage;
                button = Html.span("fakeLink", " (" + $T("Show") + ")");
                button.observeClick(function(){
                    self.show.set(true);
                });
            }
            return Html.span({}, message, button);
        });

        return this.IWidget.prototype.draw.call(this, content);
    }
},
    function(text, hiddenMessage, initialShow) {
        this.text = text;
        this.hiddenMessage = hiddenMessage;
        this.show = $V(initialShow);
    }
);


/**
 * This widget displays a text with a (Hide) fakelink next to it.
 * If the (Hide) fakelink is clicked, a message will appear and the (Hide) button will change to (Show)
 * Example of usage: we want to display a password to a user but show it initially hidden
 *
 * @param {String} text The text that we want to optionally show or not.
 * @param {String} hiddenMessage The text to show when "text" is hidden.
 * @param {Boolean} true if we want to show the text initially, false otherwise
 */
type("ShowablePasswordField", ["IWidget", "ErrorAware"], {

    _setErrorState: function(text) {
        if (this.show) {
            this._stopErrorList = this._setElementErrorState(this.clearTextField, text);
        } else {
            this._stopErrorList = this._setElementErrorState(this.passwordField, text);
        }
    },

    getName: function() {
        return this.name;
    },

    set: function(newPassword) {
        this.passwordField.dom.value = newPassword;
        this.clearTextField.dom.value = newPassword;
        this.setError(false);
    },

    get: function(newPassword) {
        if (this.show) {
            return this.clearTextField.dom.value;
        } else {
            return this.passwordField.dom.value;
        }
    },

    refresh: function() {
        if (this.show) {
            this.button.set(" (" + $T("Hide") + ")");
            this.inputDiv.set(this.clearTextField);
        } else {
            this.button.set(" (" + $T("Show") + ")");
            this.inputDiv.set(this.passwordField);
        }
    },

    draw: function() {
        var self = this;

        this.inputDiv = Html.div({style:{display:'inline'}});

        // We do not use $B and $V for the password because of a bug with two dual bindings between 2 XElements and a $V
        this.passwordField = Html.input('password', {name: this.name, id:this.id}, this.initialPassword);
        this.clearTextField = Html.input('text', {name: this.name, id:this.id}, this.initialPassword);

        this.button = Html.span("fakeLink");

        this.button.observeClick(function(){
            if (self.show) {
                self.passwordField.set(self.clearTextField.get());
            } else {
                self.clearTextField.set(self.passwordField.get());
            }
            self.show = !self.show;
            self.refresh();
            self.setError(false);
        });

        this.refresh();

        var content = Html.div({style:{display:"inline"}}, this.inputDiv, this.button);
        return this.IWidget.prototype.draw.call(this, content);
    }
},
    function(name, initialPassword, initialShow, id) {
        this.name = name;
        this.initialPassword = initialPassword;
        this.show = initialShow;
        this.id = id?id:'';

        this.invalidFieldTooltips = [];
        this.invalidFieldObserverDetachers = [];
    }
);


type("TypeSelector", ["IWidget", "WatchAccessor", "ErrorAware"],
{

    _checkErrorState: function() {
        if (this.selectOn) {
            return null;
        } else {
            return this.text._checkErrorState();
        }
    },

    setError: function(text) {
        this.text.setError(text);
    },

    draw: function() {
        var self = this;

        var chooser = new Chooser(new Lookup({
            select: function() {
                self.selectOn = true;

                self._notifyObservers(self.select.get());

                return Html.div({}, self.select,
                         " ",
                         $T("or"),
                         " ",
                         Widget.link(command(function() {
                             chooser.set('write');
                             self.text.setFocus();
                         }, $T("other"))));
            },

            write: function() {
                bind.detach(self.select);
                self.selectOn = false;

                self._notifyObservers(self.text.get());

                return Html.div({}, self.text.draw(),
                                " ",
                               $T("or"),
                               " ",
                                Widget.link(command(function() {
                                    chooser.set('select');
                                    self.select.dom.focus();
                                }, $T("select from list"))));
            }
        }));
        chooser.set('select');

        return Widget.block(chooser);
    },

    isSelect: function(){
        var self = this;
        return self.selectOn;
    },

    _notifyObservers: function(value) {
        each(this.observers,
             function(observer) {
                 observer(value);
             });
    },

    set: function(value) {
        if(this.selectOn){
            this.select.set(value);
        } else {
            this.text.set(value);
        }

        this._notifyObservers(value);
    },

    get: function() {
        var self = this;
        if(self.selectOn){
            return self.select.get();
        }
        else{
            return self.text.get();
        }
    },

    observe: function(callback) {
        var self = this;
        this.observers.push(callback);

        this.select.observe(
            function(value) {
                if (self.selectOn) {
                    callback(value);
                }
            });

        this.text.observe(
            function(value) {
                if (!self.selectOn) {
                    callback(value);
                }
            });

    },

    getSelectBox: function() {
        return this.select;
    },

    plugParameterManager: function(parameterManager) {
        this.ErrorAware.prototype.plugParameterManager.call(this, parameterManager);
    }
},
     function(types, selParams, textParams){
         selParams = selParams || {};
         textParams = textParams || {};

         this.select = bind.element(Html.select(selParams),
                                    $L(types),
                                    function(value) {
                                        return Html.option({'value': value[0]}, value[1]);
                                    });

         textParams.id = Html.generateId();

         this.text = new RealtimeTextBox(textParams);

         // just to avoid defining yet another class
         this.text._checkErrorState = function() {
             if (this.get() !== '') {
                 return null;
             } else {
                 return $T('Please select a material type');
             }
         };

         this.selectOn = true;
         this.types = types;

         this.observers = [];

     }
    );

type("InlineEditWidget", ["InlineRemoteWidget"],
     {

         setMode: function(mode) {
             if(mode == 'edit' && isFunction(this.beforeEdit)) {
                 if(this.beforeEdit() === false) {
                     return;
                 }
             }
             this.modeChooser.set(mode);
         },

         _buildFrame: function(modeChooser, switchChooser) {
             return Html.span({},
                             modeChooser,
                              Html.div({style: this.frameAttrs},
                                       switchChooser));

         },

         _handleError: function(error) {
             this._error(error);
         },

         _handleContentEdit: function() {

             var self = this;

             this.saveButton = Widget.button(command(function() {
                     if (self._verifyInput()){
                         // save it, in case we need to come back to edit mode;
                         self._savedValue = self._getNewValue();
                         self.source.set(self._savedValue);
                     }
             }, 'Save'));

             var editButtons = Html.span({},
                                         this.saveButton,
                                         Widget.button(command(function() {
                                             // back to the start
                                             self.setMode('display');
                                         }, 'Cancel')));


             // there are two possible states for the "switch" area

             return this._buildFrame(self._handleEditMode(self.value),
                                     editButtons);

         },

         _handleContentDisplay: function() {

             var self = this;
             return this._buildFrame(self._handleDisplayMode(self.value),
                                     Widget.link(command(function() {
                                         self.setMode('edit');
                                         return false;
                                     }, '(edit)')));
         },

         _handleContent: function(mode) {

             var self = this;

             // there are two possible widget modes: edit and display
             this.modeChooser = new Chooser(new Lookup(
                 {
                     'edit': function() { return self._handleContentEdit(); },
                     'display': function() { return self._handleContentDisplay(); }
                 }));

             // start in display mode
             this.modeChooser.set('display');

             return Widget.block(this.modeChooser);
         },

         /* By default, any input is accepted */
         _verifyInput: function() {
             return true;
         },


         /* Enables/disables saving */
         _setSave: function(state) {
             this.saveButton.dom.disabled = !state;
         },

         _handleLoading: function() {
             // display a progress indicator
             return progressIndicator(true, false);
         },

         _handleLoaded: function(result) {
             // save the final value once and for all
             if (exists(result.hasWarning) && result.hasWarning === true) {
                 var popup = new WarningPopup(result.warning.title, result.warning.content);
                 popup.open();
                 this.value = result.result;
             } else {
                 this.value = result;
             }
         }

     },
     function(method, attributes, initValue, beforeEdit) {
         this.frameAttrs = {'display': 'inline', 'marginLeft': '5px'};
         this.value = initValue;
         this.beforeEdit = beforeEdit;
         this.InlineRemoteWidget(method, attributes, false);
     });

type("SupportEditWidget", ["InlineEditWidget"],
        {
            /* builds the basic structure for both display and
               edit modes */
            __buildStructure: function(captionValue, emailValue) {
                // keep everything in separate lines
                 return Html.table({},
                         Html.tbody({},
                                 Html.tr("support",
                                         Html.td("supportEntry", "Caption :"),
                                         Html.td({}, captionValue)),
                                 Html.tr("support",
                                         Html.td("supportEntry", "Email :"),
                                         Html.td({}, emailValue))));
            },

            _handleEditMode: function(value) {

                // create support fields and set them to the values transmitted
                this.caption = Html.edit({}, value.caption);
                this.email = Html.edit({}, value.email);


                // add the fields to the parameter manager
                this.__parameterManager.add(this.caption, 'text', false);
                this.__parameterManager.add(this.email, 'emaillist', true);

                // call buildStructure with modification widgets
                return this.__buildStructure(this.caption, this.email);
            },

            _handleDisplayMode: function(value) {
                // call buildStructure with spans
                return this.__buildStructure(value.caption, value.email);
            },

            _getNewValue: function() {
                // clean the email list from its separators. This function is mostly used
                // for formatting the list when saving support emails asynchronously

                // removes separators at the beginning and at the end
                emaillist = this.email.get().replace(/(^[ ,;]+)|([ ,;]+$)/g, '');
                // replaces all the other groups of separators by commas
                emaillist = emaillist.replace(/[ ,;]+/g, ',');

                return {caption: this.caption.get(),
                        email: emaillist};
            },

            _verifyInput: function() {
                if (!this.__parameterManager.check()) {
                    return false;
                }
                return true;
            }
        },
        function(method, attributes, initValue) {
            this.InlineEditWidget(method, attributes, initValue);
            this.__parameterManager = new IndicoUtil.parameterManager();
        });

/*
 * This class implements a widget that lets the user edit the title
 * of a session.
 */
type("SessionRenameWidget", ["InlineWidget"],
        {
            setMode: function(mode) {
                this.modeChooser.set(mode);
                // Adjust the height of the parent container (which is a popup) and
                // prevent the appearance of a scroll bar.
                var contentHeight = this.parentContainer.content.dom.offsetHeight;
                this.parentContainer.contentWrapper.setStyle('height', pixels(contentHeight));
            },

            _buildFrame: function(modeChooser, switchChooser) {
                return Html.div({},
                            modeChooser,
                                Html.div({style:{marginTop: '5px', marginLeft: '5px', display: 'inline'}},
                                     switchChooser));
            },

            /* builds the basic structure for both display and
            edit modes */
            __buildStructure: function(sessionTitleValue) {

                return Html.div({style:{display:'inline'}},
                     Html.span("sessionRenameEntry", $T("This slot belongs to the session ")),
                     Html.span("sessionRenameValue", sessionTitleValue));

            },

            draw: function() {
                var self = this;

                var content = this._handleContent();

                // if the widget is set to load on startup,
                // the content will be a 'loading' message
                var wcanvas = Html.div({}, content);

                return wcanvas;
            },

            _handleContent: function(mode) {

                var self = this;

                // there are two possible widget modes: edit and display
                this.modeChooser = new Chooser(new Lookup(
                    {
                        'edit': function() { return self._handleContentEdit(); },
                        'display': function() { return self._handleContentDisplay(); }
                    }));

                // start in display mode
                this.modeChooser.set('display');

                return Widget.block(this.modeChooser);
            },

            _handleContentEdit: function() {

                var self = this;

                return this._buildFrame(self._handleEditMode(self.value), '');

            },

            _handleContentDisplay: function() {

                var self = this;
                return this._buildFrame(self._handleDisplayMode(self.value),
                                        Widget.link(command(function() {
                                            self.setMode('edit');
                                            return false;
                                        }, $T('(rename Session)'))));
            },

            _handleEditMode: function(value) {

                // create field and set it to the value transmitted
                this.sessionTitle = Html.edit({}, value);

                // add the field to the parameter manager
                this.__parameterManager.add(this.sessionTitle, 'text', false);

                // bind it to the info of the form
                $B(this.info.accessor('sessionTitle'), this.sessionTitle);

                // call buildStructure with modification widgets
                return this.__buildStructure(this.sessionTitle);
            },

            _handleDisplayMode: function(value) {
                var val = value;
                // truncate the title if longer than 20 characters
                if( val.length > 20 ) {
                    val = val.substr(0,17) + '...';
                }
                return this.__buildStructure("'"+val+"'");
            }

        },
        function(initValue, parameterManager, parentContainer, info) {
            this.value = initValue;
            this.parentContainer = parentContainer;
            this.__parameterManager = parameterManager;
            this.info = info;
    });


//Textarea widget
type("TextAreaEditWidget", ["InlineEditWidget"],
        {
            _handleEditMode: function(value) {
				this.textarea = Html.textarea({rows: 7, cols: 50}, value);
				this.__parameterManager.add(this.textarea, 'text', true);
                return this.textarea;
            },

            _handleDisplayMode: function(value) {
                if (value) {
                    this.comments = Html.span({}, value);
                    return this.comments;
                } else {
                    return;
                }

            },

            _getNewValue: function() {
                return this.textarea.get();
            },

            _verifyInput: function() {
                return this.__parameterManager.check();
            }
        },
        function(method, attributes, initValue) {
            this.InlineEditWidget(method, attributes, initValue);
            this.frameAttrs = {'display': 'block', 'marginTop': '5px'};
            this.__parameterManager = new IndicoUtil.parameterManager();
        });


// Select widget
type("SelectEditWidget", ["InlineEditWidget"],
        {
            _handleEditMode: function(value) {
                var content = Html.span({style:{paddingBottom:'3px'}});
                var option;
                this.select = Html.select();
                var functionDict = function(key, caption) {
                    option = Html.option({value:key}, caption);
                    self.select.append(option);
                    if (self.currentValue == caption) {
                        option.dom.selected = true;
                    }};
                var self = this;
                if(self.options.Dictionary){
                    self.options.each(functionDict);
                }
                else{
                    jQuery.each(this.options, functionDict);
                }
                content.append(this.select)
                return content;
            },

            _handleDisplayMode: function(value) {
                if(this.options.Dictionary){
                    this.currentValue = this.options.get(value);
                }
                else{
                    this.currentValue = this.options[value];
                }
                return Html.span({}, this.currentValue);
            },

            _getNewValue: function() {
                return this.select.get();
            },

            _handleSuccess: function() {
                if (this.successHandler) {
                    return this.successHandler();
                }
            },

            getCurrentValue: function() {
                return this.currentValue;
            }
        },
        function(method, attributes, options, initValue, successHandler) {
            this.options = options;
            this.initValue = initValue;
            this.successHandler = successHandler;
            this.currentValue = this.options[this.initValue];
            this.InlineEditWidget(method, attributes, initValue);
        });


// Input edit widget
type("InputEditWidget", ["InlineEditWidget", "ErrorAware"],
        {
            _handleEditMode: function(value) {
                var content = Html.div({style:{paddingBottom:'3px', marginLeft: '5px'}});
                this.input = Html.input('text', {size: 30}, value);
                content.append(this.input);
                if (this.helpMsg) {
                    var help = Html.div({style:{paddingTop:'3px'}}, Html.small({}, this.helpMsg));
                    content.append(help);
                }
                return content;
            },

            _handleDisplayMode: function(value) {
                if(str(value)!=""){
                    var content = Html.span({}, value);
                }
                else{
                    var content = Html.em({}, "No text");
                }
                return content;
            },

            _getNewValue: function() {
                return this.input.get();
            },

            _handleSuccess: function() {
                if (this.successHandler) {
                    return this.successHandler();
                }
            },

            _checkErrorState: function() {
                if (this.validation) {
                    return !this.validation(this.input.get());
                } else {
                    // No validation function
                    return false;
                }
            },

            _setErrorState: function(text) {
                this._stopErrorList = this._setElementErrorState(this.input, text);
            },

            _verifyInput: function() {
                if (!this.allowEmpty && this.input.get() == '') {
                    this._setErrorState($T('Field is mandatory'));
                    return false;
                }
                if (this._checkErrorState()) {
                    this._setErrorState(this.errorMsg);
                    return false;
                } else {
                    return true;
                }
            }
        },
        function(method, attributes, initValue, allowEmpty, successHandler, validation, errorMsg, helpMsg, beforeEdit) {
            this.attributes = attributes;
            this.allowEmpty = allowEmpty;
            this.successHandler = successHandler;
            this.validation = validation;
            this.errorMsg = errorMsg;
            this.helpMsg = helpMsg;
            this.InlineEditWidget(method, attributes, initValue, beforeEdit);
        });

type("URLPathEditWidget", ["InputEditWidget"],
        {
            _handleDisplayMode: function(value) {
                var self = this;
                var content = "";
                if(value !=""){
                    content = Html.span({}, self.basePath + value);
                } else{
                    content = Html.em({}, $T("There is not any short url yet. Click \"edit\" to setup."));
                }
                return content;
            }
        },
        function(method, attributes, basePath, initValue, allowEmpty, successHandler, validation, errorMsg, helpMsg, beforeEdit) {
            this.basePath = basePath;
            this.InputEditWidget(method, attributes, initValue, allowEmpty, successHandler, validation, errorMsg, helpMsg, beforeEdit);
        });



type('AutocheckTextBox', ['RealtimeTextBox'],
        /*
         * A usual text box that, when the startWatching method is called,
         * will inform the user in case that what he writes is the same string
         * the text box had when startWatching was called.
         */
        {
            /*
             * Called each time a new character is typed
             * strips white spaces, and calls for a request if needed
             */
            _textTyped: function(key) {

                var self = this;
                var text = trim(this.get());
                if(text.length > 1) {
                    if(text != self.originalText){
                        if (exists(self.functionToHide)){
                            self.functionToHide(self.component);
                        }
                        else{
                            self.component.dom.style.display = "none";
                        }
                    }
                    else{
                        if (exists(self.functionToShow)){
                            self.functionToShow(self.component);
                        }
                        else{
                            self.component.dom.style.display = '';
                        }
                    }

                }
            },

            setOriginalText: function(text){
                this.originalText = text;
            },

            startWatching: function(isRepeated, originalText){
                var self = this;

                //we set the text with which we will compare before doing the observe
                self.setOriginalText(originalText == null?self.get():originalText);
                if (isRepeated){
                    if (exists(self.functionToShow)){
                        self.functionToShow(self.component);
                    }
                    else{
                        self.component.dom.style.display = '';
                    }
                }
                else{
                    if (exists(self.functionToHide)){
                        self.functionToHide(self.component);
                    }
                    else{
                        self.component.dom.style.display = "none";
                    }
                }

                self.observe(function(key, event) {
                    self._textTyped(key);
                    return true;
                });
		    }
		},

		    function(args, component, functionToShow, functionToHide){
				/* component: The component (usually a simple label) that you want to
				   inform the user that the original text field is repeated
				   functionToShow: In case that your component requires some other operations to accomplish what you
				   want rather than just setting the display to none, you'll need to specify what do you want to do.
				   functionToHide: the same thing when hiding the component.
				*/
				args.autocomplete = 'off';
				this.RealtimeTextBox(args);
				this.setOriginalText(this.get());
				this.component = component;
				this.functionToShow = functionToShow;
				this.functionToHide = functionToHide;
		     }
	);
