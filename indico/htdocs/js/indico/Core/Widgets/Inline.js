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

type("SwitchOptionButton", ["InlineWidget"],
     {
         draw: function() {
             var self = this;
             var checkbox = $("<input/>").attr("type","checkbox").css("vertical-align", "middle");
             var message = $("<span/>").css({"color":"green", "margin-left":"10px", "vertical-align":"middle", "display": "none"}).append(self.savedMessage);
             var tbody = $("<tbody/>");
             tbody.append($("<tr/>").append($("<td/>").append(checkbox).append($("<span/>").css("vertical-align", "middle").append(this.caption))).append($("<td/>").append(message)));

             var request = function(args, showSavedMessage) {
                 indicoRequest(self.method,
                         args, function(response, error){
                       if (exists(error)) {
                           self._error(error);
                       }
                       else {
                           checkbox.prop("checked", response);
                           if(showSavedMessage){
                               message.show();
                               setTimeout(function(){message.hide();}, 1000);
                           }
                       }
                   });
             };


             checkbox.prop('disabled', this.disabled);

             if(this.initState !== null){
                 checkbox.prop("checked", this.initState);
             } else{
                 request(self.attributes, false);
             }

             if(this.disabled) {
                 $(tbody).qtip({content: $T("You do not have access to modify the value of this checkbox"), position: {my: 'top middle', at: 'bottom middle'}});
             }

             checkbox.click(function(){
                 self.attributes.set('value', checkbox.is(":checked"));
                 request(self.attributes, true);
             });

             return $("<table/>").css("display","inline").append(tbody).get(0);
         }

     },
     function(method, attributes, caption, savedMessage, initState, disabled) {
         this.method = method;
         this.attributes = $O(attributes);
         this.caption = caption;
         this.savedMessage = savedMessage;
         this.initState = initState;
         this.disabled = disabled;
     });


type("SelectRemoteWidget", ["InlineRemoteWidget", "WatchAccessor", "ErrorAware"],
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

         _setErrorState: function(text) {
             this._stopErrorList = this._setElementErrorState(this.select, text);
         },

         _drawNoItems: function() {
             var option = Widget.option(new WatchPair("None", this.noOptionsText));
             option.accessor('disabled').set("disabled");
             option.accessor('selected').set("selected");
             return option;
         },

         _handleContent: function() {
             var self = this;

             var options = this.source.get();

             if(_.size(self.source.get()) > 0){
                 bind.element(this.select,
                                     this.source,
                                     function(item) {
                                         if ($.isArray(item)) {
                                             item = new WatchPair(item[0], item[1]);
                                         } else if(!item.key) {
                                             item = new WatchPair(item, item);
                                         }
                                         return self._drawItem(item);
                                     });
                 if(self.select.dom.value != self.selected.get() && self.showNoValue){
                     var option  = Widget.option(new WatchPair("", ""));
                     self.select.append(option);
                     option.accessor('selected').set("selected");
                 }
                 return self.select;
             } else{
                 self.select.append(self._drawNoItems());
                 return self.select;

             }
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
         },
         getName: function() {
             return this.name;
         }

     },
     function(method, args, callback, name, noOptionsText, defaultSelected, showNoValue) {
         this.select = Html.select({'name':name});
         this.selected = new WatchValue();
         if(defaultSelected !== undefined){
             this.set(defaultSelected);
         }
         this.noOptionsText = any(noOptionsText,$T("No options"));
         // Load data source on startup
         this.InlineRemoteWidget(method, args, true, callback);
         this.loadOnStartup = false;
         this.name = name;
         this.showNoValue = any(showNoValue, true);
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
         onChange: function(callback){
             this.input.observeEvent('change',callback);
         }
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


type("InlineEditWidget", ["InlineRemoteWidget"],
     {

         setMode: function(mode) {
             if(mode == 'edit' && isFunction(this.beforeEdit)) {
                 if(this.beforeEdit(this) === false) {
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

         /* By default, any check before save is accepted */
         _handleSave: function() {
             this._save();
         },

         _save: function() {
             this._savedValue = this._getNewValue();
             this.source.set(this._savedValue);
         },

         _handleContentEdit: function() {

             var self = this;

             this.saveButton = Widget.button(command(function() {
                     if (self._verifyInput()){
                         // save it, in case we need to come back to edit mode;
                         self._handleSave();
                     }
             }, $T('Save')));

             var editButtons = Html.span({},
                                         this.saveButton,
                                         Widget.button(command(function() {
                                             // back to the start
                                             self.setMode('display');
                                         }, $T('Cancel'))));


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
                                     }, $T('(edit)'))));
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
            __buildStructure: function(captionValue, emailValue, phoneValue) {
                // keep everything in separate lines
                 return Html.table({},
                         Html.tbody({},
                                 Html.tr("support",
                                         Html.td("supportEntry", "Caption :"),
                                         Html.td({}, captionValue)),
                                         Html.tr("support",
                                                 Html.td("supportEntry", "Email :"),
                                                 Html.td({}, emailValue)),
                                         Html.tr("support",
                                                 Html.td("supportEntry", "Telephone :"),
                                                 Html.td({}, phoneValue))));
            },

            _handleEditMode: function(value) {

                // create support fields and set them to the values transmitted
                this.caption = Html.edit({}, value.caption);
                this.email = Html.edit({}, value.email);
                this.phone = Html.edit({}, value.telephone);


                // add the fields to the parameter manager
                this.__parameterManager.add(this.caption, 'text', false);
                this.__parameterManager.add(this.email, 'emaillist', true);
                this.__parameterManager.add(this.phone, 'phone', true);

                // call buildStructure with modification widgets
                return this.__buildStructure(this.caption, this.email, this.phone);
            },

            _handleDisplayMode: function(value) {
                // call buildStructure with spans
                return this.__buildStructure(value.caption, value.email, value.telephone);
            },

            _getNewValue: function() {
                // clean the email list from its separators. This function is mostly used
                // for formatting the list when saving support emails asynchronously

                // removes separators at the beginning and at the end
                var emaillist = this.email.get().replace(/(^[ ,;]+)|([ ,;]+$)/g, '');
                // replaces all the other groups of separators by commas
                emaillist = emaillist.replace(/[ ,;]+/g, ',');

                return {caption: this.caption.get(),
                        email: emaillist,
                        telephone: this.phone.get()};
            },

            _verifyInput: function() {
                return this.__parameterManager.check();
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
                //var contentHeight = this.parentContainer.content.dom.offsetHeight;
                //this.parentContainer.contentWrapper.setStyle('height', pixels(contentHeight));
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
                return Html.div({}, content);
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
                    // start by escaping the input
                    var dummy = $('<span/>').text(value);
                    value = dummy.html();

                    // now transform double line breaks into paragraphs
                    value = '<p>' + value.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br/>') + '</p>';
                    return Html.unescaped.span({}, value);
                } else {
                    return;
                }
            },

            _handleBackToEditMode: function() {
                this.textarea.set(this._savedValue);
            },

            _handleSuccess: function() {
                if (this.successHandler) {
                    return this.successHandler();
                }
            },

            _getNewValue: function() {
                return this.textarea.get();
            },

            _verifyInput: function() {
                return this.__parameterManager.check();
            }
        },
        function(method, attributes, initValue, successHandler, beforeEdit) {
            this.InlineEditWidget(method, attributes, initValue, beforeEdit);
            this.frameAttrs = {'display': 'block', 'marginTop': '5px'};
            this.successHandler = successHandler;
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
                content.append(this.select);
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
                    var content = Html.em({}, $T("No text"));
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
                    content = Html.em({}, $T("There is no short url yet."));
                }
                return content;
            }
        },
        function(method, attributes, basePath, initValue, allowEmpty, successHandler, validation, errorMsg, helpMsg, beforeEdit) {
            this.basePath = basePath;
            this.InputEditWidget(method, attributes, initValue, allowEmpty, successHandler, validation, errorMsg, helpMsg, beforeEdit);
        });
