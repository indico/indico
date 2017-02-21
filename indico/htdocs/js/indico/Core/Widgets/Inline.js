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


;
