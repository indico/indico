type("ChainedPopupWidget", ["PopupWidget"],
     {
         clickTriggersClose: function(target) {

             var result = true;

             // check chain
             each(this.chainElements,
                  function(element) {
                      // since usually the first element of the chain is an Html.a...
                      element = element.ChainedPopupWidget?element.canvas:element;
                      result = result && !element.ancestorOf(target);
                  });

             return result && !this.canvas.ancestorOf(target);
         },

         open: function(x, y) {
             var self = this;

             if (this.active) {
                 // don't let the popup open twice
                 return;
             } else {
                 this.active = true;
             }

             this.PopupWidget.prototype.open.call(this, x, y);

             // define a handler for onclick events
             this.handler = function(event) {
                 if (self.clickTriggersClose($E(eventTarget(event)))) {
                     // if the click should be followeb by a
                     // closing action (out of the chain)
                     self.close();

                     // call close() over the whole chain
                     each(self.chainElements, function(element) {
                         if (element.ChainedPopupWidget) {
                             element.close();
                         }
                     });
                 }
             }

             IndicoUtil.onclickHandlerAdd(this.handler);
         },
         
         postDraw: function () {
             if (this.alignRight) {
                 // Hide it to avoid flickering
                 this.canvas.dom.style.visibility = 'hidden';
                 
                 // Place it to the left in order to measure the width
                 // if placed to the right it might be to wide for the page
                 this.canvas.dom.style.left = 0;
                 
                 // Align right side of the canvas to the x position given
                 this.canvas.dom.style.left = pixels(this.x - this.canvas.dom.offsetWidth);

                 this.canvas.dom.style.visibility = 'visible';
             }
         },

         close: function() {
             // close() cleans up the onclick handler too
             this.active = false;
             IndicoUtil.onclickHandlerRemove(this.handler);
             this.PopupWidget.prototype.close.call(this);
         }

     },
     function(chainElements, alignRight) {
         this.PopupWidget();
         this.chainElements = chainElements;
         this.active = false;
         this.alignRight = any(alignRight, false);
     });

type("PopupMenu", ["ChainedPopupWidget"],
     {
         draw: function(x, y) {
             var self = this;

             // create an Html.ul from the items that
             // were provided through the constructor
             var content = $B(Html.ul(self.cssClass), this.items,
                 function(pair) {
                     var value = pair.get();
                     var link = Html.a({href: '#'}, pair.key);
                     
                     if(typeof value == "string" ) {
                         link.setAttribute('href', value);
                         if (self.closeOnClick) {
                             link.observeClick(function() {
                                 self.close();
                             });
                         }
                     }
                     else {
                         link.observeClick(pair.get().PopupWidget?
                                           function(e) {
    
                                               if (self.selected) {
                                                   self.selected.dom.className = null;
                                                   self.selected = null;
                                               }
    
                                               link.dom.className = 'selected';
                                               self.selected = link;
    
                                               var pos = listItem.getAbsolutePosition();
    
                                               each(self.items, function(item, key) {
                                                   if (item.isOpen()) {
                                                       item.close();
                                                   }
                                               });
    
                                               IndicoUtil.onclickHandlerRemove(self.handler);
                                               pair.get().open(pos.x + link.dom.offsetWidth, pos.y - 1);
                                               
                                               if (self.closeOnClick) {
                                                   self.close();
                                               }
                                               
                                               return false;
                                           }:
                                           function() {
                                               // assume it's a callback function
                                               pair.get()(self);
                                           });
                     }

                     var listItem = Html.li({},
                         link);
                     return listItem;
                 });

             return this.PopupWidget.prototype.draw.call(this, content, x, y);

         }
     },
     function(items, chainElements, cssClass, closeOnClick, alignRight) {
         this.ChainedPopupWidget(chainElements, alignRight);
         this.items = items;
         this.selected = null;
         this.cssClass = "popupList " + any(cssClass,"");
         this.closeOnClick = any(closeOnClick, false);
     });

type("RadioPopupWidget", ["ChainedPopupWidget"],
     {
         draw: function(x, y) {

             var self = this;
             var optionsId = Html.generateId();

             // need to store radiobuttons, for IE compatibility
             // purposes
             this.radioButtons = {};

             var content = $B(Html.ul({className: "popupList", style: {padding: pixels(2)}}),
                 this.states,
                 function(pair) {
                     var optionRadio = Html.radio({name:optionsId});

                     self.radioButtons[pair.key] = optionRadio;

                     optionRadio.observe(function(value) {
                         if (value) {
                             self.accessor.set(pair.key);
                         }
                     });

                     return Html.li({},
                                    Html.span({style: {padding: '0px 4px 2px 0px'}}, optionRadio, pair.get()));
                 });

             return this.PopupWidget.prototype.draw.call(this, content, x, y);
         },

         postDraw: function() {
             // called after all the rendering is done
             var self = this;

             each(this.radioButtons, function(radio, key) {
                 if (self.accessor.get() == key) {
                     radio.set(true);
                 }
             });
         }
     },

     function(states, accessor, chainElements) {
         this.ChainedPopupWidget(chainElements);
         this.states = states;
         this.accessor = accessor;
     });

type("CheckPopupWidget", ["ChainedPopupWidget"],
     {
         draw: function(x, y, maxHeight, styles) {

             var self = this;
             var optionsId = Html.generateId();

             // need to store checkboxes, for IE compatibility
             // purposes
             this.checkboxes = {};

             if (this.options.isEmpty() && this.noOptionsMessage) {
                 var content = Html.ul({className: "popupList",
                     style: {maxHeight: pixels(maxHeight), fontStyle: 'italic', color: '#444444', padding: pixels(5)}},
                     this.noOptionsMessage);
                 return this.PopupWidget.prototype.draw.call(this, content, x, y, styles);
             }
             var content = $B(Html.ul({
                 className: "popupList",
                 style: {maxHeight: pixels(maxHeight), overflowY: 'auto', overflowX: 'hidden', padding: pixels(2)}
             }),
                              this.options,
                              function(pair) {
                                  var optionCheck = Html.checkbox({});
				  				  optionCheck.dom.name = optionsId;

                                  self.checkboxes[pair.key] = optionCheck;
                                  $B(optionCheck, self.object.accessor(pair.key));

                                  return Html.li({},
                                                 Html.span({style: {padding: '0px 4px 2px 0px'}}, optionCheck, pair.get()));
                              }
                             );

             return this.PopupWidget.prototype.draw.call(this, content, x, y, styles);
         },

         postDraw: function() {
             // called after all the rendering is done
             var self = this;

             each(this.checkboxes, function(check, key) {
                 if (self.object.get(key)) {
                     check.set(true);
                 }
             });
         }
     },

     function(options, object, chainElements, noOptionsMessage) {
         this.ChainedPopupWidget(chainElements);
         this.options = options;
         this.object = object;

         // A message to be shown if the the dict of options is empty
         this.noOptionsMessage = any(noOptionsMessage, null);
     });
