// TODO
/*
type("ColoredCheckbox", ["Html"],
     {
         _draw: function() {
             return Html.span({},
                             );
         }
     },
     function(attributes, checked, label) {
         this.checkbox = Html.checkbox(attributes, checked);
         this.label = label;
     });

IndicoUI.Widgets.Inline = {
    coloredCheckbox: function(attributes, checked, label) {
        return new ColoredCheckbox(attributes, checked, label).draw();
    }
}
*/
// *******************************

type("InlineWidget", ["IWidget"],
     {
         _error: function(error) {
             var dialog = new ErrorReportDialog(error);
             dialog.open();
         }
     });


type("InlineRemoteWidget", ["InlineWidget"],
     {
         draw: function() {
             var self = this;
             var canvas = Html.span({}, 'loading...');

             this.source.state.observe(function(state) {
                 if (state == SourceState.Error) {
                     self.ready.set(true);
                     self._error(self.source.error.get());
                 } else if (state == SourceState.Loaded) {
                     self.ready.set(true);
                     canvas.set(self.drawContent());
                 } else {
                     self.ready.set(false);
                     canvas.set('loading...');
                 }
             });

             return canvas;
         }

     },
     function(method, attributes) {
         this.ready = new WatchValue();
         this.ready.set(false);
         this.source = indicoSource(method, attributes);
     });

type("SwitchOptionButton", ["InlineRemoteWidget"],
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
     function(method, attributes, caption) {
         this.InlineRemoteWidget(method, attributes);
         this.caption = caption;
         this.checkbox = Html.checkbox({});

         $B(this.checkbox, this.source);
     });

type("RadioFieldWidget", ["InlineWidget"],
     {
         draw: function() {
             var self = this;

             return $B(Html.ul(this.cssClassRadios),
                       this.orderedItems,
                       function(item) {
                           var radio = self.radioDict[item.key];
                           radio.observeClick(function() {
                               self.select(item.key);
                           });
                           self.options.accessor(item.key).observe(
                               function(value) {
                                   radio.set(value);
                               });

                           var itemContent = item.get();

                           if (itemContent.IWidget) {
                               itemContent = itemContent.draw();
                           }

                           // create li item, add visibility info too
                           var liItem = Html.li(self.visibility.get(item.key)?{}:'disabledRadio', keys(self.radioDict).length > 1?radio:'', itemContent);
                           radio.dom.disabled = !self.visibility.get(item.key);


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
                       });
         },

         setVisibility: function(key, visible) {
             this.visibility.set(key, visible);
         },

         onSelect: function(state) {
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

     function(items, order, cssClassRadios) {
         this.items = items;
         this.radioDict = {};
         this.options = new WatchObject();
         this.visibility = new WatchObject();
         this.cssClassRadios = exists(cssClassRadios)?cssClassRadios:'nobulletsList';

         var self = this;


         var name = Html.generateId();

         // consider ordering of elements, if specified
         if (order) {
             this.orderedItems = $L();
             each(order,
                  function(key) {
                      self.orderedItems.append(new WatchPair(key, items[key]));

                      // add some extra stuff, since we're in the loop
                      self.visibility.set(key, true);
                      self.options.set(key, false);
                      self.radioDict[key] = Html.radio({'name': name});
                  });

         } else {
             this.orderedItems = $L(items);
         }

         this.state = new Chooser(map(items,
                                      function(value, key) {
                                          return key;
                                      }));


     });

type("SelectRemoteWidget", ["InlineRemoteWidget", "WatchAccessor"],
     {
         _drawItem: function(item) {
             var option = Widget.option(item);// Html.option({value: item.key}, item.get());
             this.options.set(item.key, option);

             if (this.selected.get()) {
                 if (this.selected.get() == item.key) {
                     option.accessor('selected').set(true);
                 }
             }

             return option;
         },

         drawContent: function() {
             var self = this;

             this.selected.observe(function(value) {
                 var elem = self.options.get(value);

                 if (elem) {
                     elem.accessor('selected').set(true);
                 }
             });

             return bind.element(this.select,
                                 this.source,
                                 function(item) {
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
     function(method, args) {
         this.options = new WatchObject();
         this.select = Html.select({});
         this.selected = new WatchValue();
         this.InlineRemoteWidget(method, args);
     });

type("FavoriteSelectRemoteWidget", ["SelectRemoteWidget"],
     {
         _drawItem: function(item) {
             var option = this.SelectRemoteWidget.prototype._drawItem.call(this, item);
             // apply on widget generation/reload
             if (this.favorites && exists(this.favorites.indexOf(item.key))) {
                 option.dom.className = 'favoriteItem';
             }
             return option;
         },

         setFavorites: function(list) {

             this.favorites = list;

             var self = this;

             // apply immediately
             each(list, function(favorite) {
                 var option = self.options.get(favorite);
                 if (exists(option)){
                     option.dom.className = 'favoriteItem';
                 }
             });
         }
     },
     function(method, args) {
         this.SelectRemoteWidget(method, args);
     });


type("RealtimeTextBox", ["IWidget", "WatchAccessor"],
     {
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
         observeOtherKeys: function(observer) {
             this.otherKeyObservers.push(observer);
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
         enableEvent: function() {
             var self = this;

             this.input.observeEvent('keydown', function(event) {
                 var keyCode = event.keyCode;
                 var value = true;

                 if ((keyCode < 32 && keyCode != 8) || (keyCode >= 33 && keyCode < 46) || (keyCode >= 112 && keyCode <= 123)) {
                     each(self.otherKeyObservers, function(func) {
                         value = value && func(self.input.get(), keyCode, event);
                     });
                     return value;
                 }
                 return true;
             });


             // fire onChange event each time there's a new char
             this.input.observeEvent('keyup', function(event) {
                 var keyCode = event.keyCode;
                 var value = true;

                 if (!((keyCode < 32 && keyCode != 8) || (keyCode >= 33 && keyCode < 46) || (keyCode >= 112 && keyCode <= 123))) {
                     each(self.observers, function(func) {
                         value = value && func(self.input.get(), keyCode, event);
                     });
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
                    keyPressAction();
                }
                Dom.Event.dispatch(self.input.dom, 'change');
            });
        });

/*
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
    this.topTransparentDiv = Html.div({style:{position:"absolute",top:pixels(0), left:pixels(0), width:Browser.IE?"":"100%", height:Browser.IE?"":"100%"}})
    this.div = Html.div({style:{display:"inline", position:Browser.IE?"":"relative"}},button, this.topTransparentDiv);
}
);
