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
                 // don't let the popup open twice [** Update: It's not working ! **]
                 return;
             } else {
                 this.active = true;
             }

             this.PopupWidget.prototype.open.call(this, x, y);

             var handler = function(event) {
                 if (self.clickTriggersClose($E(eventTarget(event)))) {
                     // if the click should be followed by a
                     // closing action (out of the chain)
                     self.close();
                     // call close() over the whole chain
                     each(self.chainElements, function(element) {
                         if (element.ChainedPopupWidget) {
                             element.close();
                         }
                     });
                 }
             };

             // define a handler for onclick events
             $('html').on('click.chained_menu', handler);
             this.handler = handler;
         },

         postDraw: function () {

             this.PopupWidget.prototype.postDraw.call(this);

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
             $('html').off('click.chained_menu', this.handler);
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
        _processItem: function(pair) {
            var self = this;
            var value = pair.get();
            var link = Html.a('fakeLink', value.display);
            link.setAttribute("id", pair.key);
            link.setAttribute("title", value.description);

            if(typeof value.action == "string" ) {
                link.setAttribute('href', value.action);
                if (self.linkToExternalWindow) {
                    link.setAttribute('target', '_blank');
                }
                if (value.ajaxDialog) {
                    $(link.dom).ajaxDialog({
                        title: value.display
                    });
                }
                if (self.closeOnClick || value.closeOnClick) {
                    link.observeClick(function() {
                        self.close();
                    });
                }
            }
            else {
                link.observeClick((value.action.PopupWidget || value.action.ExclusivePopup)?
                                  function(e) {

                                      if (self.selected) {
                                          self.selected.dom.className = null;
                                          self.selected = null;
                                      }

                                      link.dom.className = 'selected';
                                      self.selected = link;
                                      var pos = listItem.getAbsolutePosition();

                                      each(self.items, function(item, key) {
                                          if (item.PopupWidget && item.isOpen()) {
                                              item.close();
                                          }
                                      });

                                      IndicoUtil.onclickHandlerRemove(self.handler);
                                      var target = pair.get().action;
                                      target.open(pos.x + (target.alignRight ? 0 : link.dom.offsetWidth), pos.y - 1);

                                      return false;
                                  }:
                                  function() {
                                      // assume it's a callback function
                                      var ret = pair.get().action(self);
                                      if ((self.closeOnClick && ret !== false) || ret === true) {
                                          self.close();
                                      }
                                  });
            }

            var listItem = null;
            if(pair.key === this.currentItem) {
                listItem = Html.li("current", link);
            }
            else {
                listItem = Html.li({}, link);
            }

            return listItem;
        },
        close: function() {
            if(this.closeHandler()) {
                this.ChainedPopupWidget.prototype.close.call(this);
            }
        },
        draw: function(x, y) {
            var self = this;

            // create an Html.ul from the items that
            // were provided through the constructor
            var content = $B(Html.ul(self.cssClass), this.items, function(pair) {
                return self._processItem(pair);
            });

            return this.PopupWidget.prototype.draw.call(this, content, x, y);
        }
    },
    function(items, chainElements, cssClass, closeOnClick, alignRight, closeHandler, currentItem, linkToExternalWindow) {
        this.ChainedPopupWidget(chainElements, alignRight);
        this.items = items;
        this.currentItem = any(currentItem, []);
        this.selected = null;
        this.cssClass = "popupList " + any(cssClass,"");
        this.closeOnClick = any(closeOnClick, false);
        this.closeHandler = any(closeHandler, function() {return true;});
        this.linkToExternalWindow = any(linkToExternalWindow, false);
    }
);

type("SectionPopupMenu", ["PopupMenu"], {
        draw: function(x, y) {
            var self = this;

            var sectionContent = Html.ul(self.cssClass);

            each(this.items, function(item, key) {
                var section = null;
                if (key !== ""){
                    section = Html.li('section', Html.div('line', Html.div('name', key)));
                    section.setAttribute('title', item['description']);
                }

                // add the menu items
                var tmp = $B(Html.ul('subPopupList'), item['content'], _.bind(self._processItem, self));
                sectionContent.append(Html.li({}, section, tmp));
            });

            return this.PopupWidget.prototype.draw.call(this, sectionContent, x, y);
        }
        },
        function(items, chainElements, cssClass, closeOnClick, alignRight, closeHandler) {
            this.ChainedPopupWidget(chainElements, alignRight);
            this.items = items;
            this.selected = null;
            this.cssClass = "popupList sectionPopupList " + any(cssClass,"");
            this.closeOnClick = any(closeOnClick, false);
            this.closeHandler = any(closeHandler, function() {return true;});
        }
);

type("CheckPopupWidget", ["ChainedPopupWidget"],
     {
         draw: function(x, y, maxHeight, styles) {

             var self = this;
             var optionsId = Html.generateId();

             // need to store checkboxes, for IE compatibility
             // purposes
             this.checkboxes = {};

             var content = null;

             if (this.options.isEmpty() && this.noOptionsMessage) {
                 content = Html.ul({className: "popupList",
                     style: {maxHeight: pixels(maxHeight), fontStyle: 'italic', color: '#444444', padding: pixels(5)}},
                     this.noOptionsMessage);
                 return this.PopupWidget.prototype.draw.call(this, content, x, y, styles);
             }
             content = $B(Html.ul({
                 className: "popupList popupListCheckboxes",
                 style: {maxHeight: pixels(maxHeight), overflowY: 'auto', overflowX: 'hidden', padding: pixels(2)}
             }),
                              this.options,
                              function(pair) {
                                  var optionCheck = Html.checkbox({});
                                                                  optionCheck.dom.name = optionsId;

                                                                  optionCheck.observeClick(function(e) {
                                                                      // Make sure the onclick event is not captured by
                                                                      // parent elements as this would undo the click on the
                                                                      // checkbox.
                                                                      if (!e) {
                                                                          e = window.event;
                                                                      }
                                                                      e.cancelBubble = true;
                                                                      if (e.stopPropagation){
                                                                          e.stopPropagation();
                                                                      }
                                                              });

                                  self.checkboxes[pair.key] = optionCheck;
                                  $B(optionCheck, self.object.accessor(pair.key));

                                  var color = self.colors.get(pair.key);
                                  if (!color){
                                      color = 'transparent';
                                  }
                                  var textColor = self.textColors.get(pair.key);
                                  if (!textColor){
                                      textColor = 'black';
                                  }

                                  //var span = Html.div({className: 'item', style: {cursor: 'pointer'}}, )
                                  var span = Html.span('wrapper', pair.get());

                                  var li = Html.li({ style: {backgroundColor: color, color: textColor, marginBottom: '2px'}}, optionCheck, span);

                                  li.observeClick(function() {
                                      self.object.set(pair.key, !self.object.get(pair.key));
                                  });
                                  return li;
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

     function(options, object, colors, textColors, chainElements, noOptionsMessage) {
         this.ChainedPopupWidget(chainElements);
         this.options = options;
         this.object = object;
         this.colors = colors;
         this.textColors = textColors;

         // A message to be shown if the the dict of options is empty
         this.noOptionsMessage = any(noOptionsMessage, null);
     });
