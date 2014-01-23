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
                if (self.closeOnClick) {
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
        drawInfoBubbles: function(infoItems){
            for(var item in infoItems){
                var span = Html.span('infoBubble');
                $E(item).append(span);
                span.dom.innerHTML = infoItems[item];
                span.dom.style.visibility = "visible";
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

/* For add Session menu popup, we add some colored squares for each session */
type("SessionSectionPopupMenu", ["SectionPopupMenu"], {
    _processItem: function(pair) {
        var self = this;
        var value = pair.get();
        var color = null;
        var title = null;

        if(exists(value.title)){
            title = value.title;
        }else {
            title = pair.key;
        }

        if(exists(value.color)){
            color = value.color;
            value = value.func;
        }

        var colorSquare = null;
        if(color !== null){
            colorSquare = Html.div({style:{backgroundColor: color, color: color, cssFloat: 'right', width: '15px', height:'15px'}});
        }

        var link = Html.a({className:'fakeLink', style:{display: 'inline', padding: 0, paddingLeft: '4px', paddingRight: '4px'}}, Util.truncate(title));
        var divInput = Html.div({style:{height:'20px', overflow:'auto'}}, colorSquare, link);

        if(typeof value == "string" ) {
            link.setAttribute('href', value);
            if (self.closeOnClick) {
                link.observeClick(function() {
                    self.close();
                });
            }
        }
        else {
            link.observeClick(value.PopupWidget?
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
                                  value.open(pos.x + (value.alignRight ? 0 : link.dom.offsetWidth), pos.y - 1);

                                  return false;
                              }:
                              function() {
                                  // assume it's a callback function
                                  value(self);
                                  if (self.closeOnClick) {
                                      self.close();
                                  }
                              });
        }

        var listItem = Html.li({},
            divInput);
        return listItem;
    }
},

     function(items, chainElements, cssClass, closeOnClick, alignRight, closeHandler) {
         this.SectionPopupMenu(items, chainElements, cssClass, closeOnClick, alignRight, closeHandler);
     }
    );

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

type("ColorPicker", ["WatchValue", "ChainedPopupWidget"], {
    defaultColors: [
        {bgColor: '#EEE0EF', textColor: '#1D041F'},
        {bgColor: '#E3F2D3', textColor: '#253F08'},
        {bgColor: '#FEFFBF', textColor: '#1F1F02'},
        {bgColor: '#DFE555', textColor: '#202020'},
        {bgColor: '#FFEC1F', textColor: '#1F1D04'},
        {bgColor: '#DFEBFF', textColor: '#0F264F'},
        {bgColor: '#0D316F', textColor: '#EFF5FF'},
        {bgColor: '#1A3F14', textColor: '#F1FFEF'},
        {bgColor: '#5F171A', textColor: '#FFFFFF'},
        {bgColor: '#D9DFC3', textColor: '#272F09'},
        {bgColor: '#4F144E', textColor: '#FFEFFF'},
        {bgColor: '#6F390D', textColor: '#FFEDDF'},
        {bgColor: '#8ec473', textColor: '#021F03'},
        {bgColor: '#92b6db', textColor: '#03070F'},
        {bgColor: '#DFDFDF', textColor: '#151515'},
        {bgColor: '#ecc495', textColor: '#1F1100'},
        {bgColor: '#b9cbca', textColor: '#0F0202'},
        {bgColor: '#C2ECEF', textColor: '#0D1E1F'},
        {bgColor: '#d0c296', textColor: '#000000'},
        {bgColor: '#EFEBC2', textColor: '#202020'}
    ],
    draw: function(x, y) {
        var self = this;

        var colorInputChanged = function(colorType, color, previewBlock) {
            if (!self._validateColor(color)) {
                previewBlock.set('x');
                previewBlock.dom.style.backgroundColor = 'transparent';
            } else {
                previewBlock.set('');
                previewBlock.dom.style.backgroundColor = color;

                var colors = clone(self.get());
                colors[colorType] = color;
                self.set(colors);
            }
        };
        var updateColorInput = function(color, inputElement, previewBlock) {
            if (!color){
                return;
            }

            previewBlock.dom.style.backgroundColor = color;
            inputElement.set(color.substr(1, color.length-1));
        };
        var createColorInput = function(colorType) {
            var input = Html.edit();
            var preview = Html.div('previewBlock');

            input.observeEvent('keyup', function() {
                colorInputChanged(colorType, '#' + input.get(), preview);
            });
            self.observe(function(colors) {
                updateColorInput(colors[colorType], input, preview);
            });

            updateColorInput(self.get()[colorType], input, preview);

            return Html.div('inputWrapper', preview, Html.div('inputContainer clearfix', Html.div('numberSign', '#'), input));
        };

        var tbody = Html.tbody({});
        var tr;
        var i = 0;
        each(self.defaultColors, function(c) {
            if (i++ % 5 === 0) {
                tr = Html.tr();
                tbody.append(tr);
            }

            var colorBlock = Html.div({className: 'block', style: {
                backgroundColor: c.bgColor,
                color: c.textColor
            }}, 'e');

            colorBlock.observeClick(function (e) {
                self.set(c);
                self.close();
            });
            tr.append(Html.td({}, colorBlock));
        });

        var div = Html.div('colorPicker');

        // Close the color picker if user presses Esc button
        div.observeEvent('keyup', function(e) {
            if (e.keyCode == 27){
                self.close();
            }
        });

        div.append(Html.table({}, tbody));

        tbody = Html.tbody({});
        var customTable = Html.table({className: 'custom', cellspacing: '0', cellpadding: '0', border: '0'}, tbody);

        tbody.append(Html.tr({}, Html.td({}, 'Block'), Html.td({}, createColorInput('bgColor'))));
        tbody.append(Html.tr({}, Html.td({}, 'Text'), Html.td({}, createColorInput('textColor'))));

        div.append(customTable);

        /*
         * If the current color is a custom color (that is, if it's not among the default ones)
         * then show the custom color fields by default
         */
        var currentColors = this.get();
        var showCustom = true;
        for (var i in this.defaultColors) {
            var colors = this.defaultColors[i];
            if (colors.textColor == currentColors.textColor &&
                colors.bgColor == currentColors.bgColor) {
                showCustom = false;
                break;
            }
        }
        if (!showCustom) {
            var customLink = Html.a({className: 'fakeLink', style: {fontSize: '0.8em'}}, 'Custom colors');
            customTable.dom.style.display = 'none';
            customLink.observeClick(function () {
                customTable.dom.style.display = 'block';
                customLink.dom.style.display = 'none';
            });
            div.append(Html.div({style: {textAlign: 'right', margin: '3px 5px'}}, customLink));
        }

        return this.PopupWidget.prototype.draw.call(this, div, x, y);
    },
    /*
     * Returns an clickable link that opens the color selector. If a onclick
     * function is provided it will be called and the color picker opened if it
     * returns true
     */
    getLink: function(onclick, text) {
        var self = this;

        text = any(text, $T('Color'));
        onclick = any(onclick, function () { return true; });

        this.link = Html.span('colorPickerLink', Html.span({},text));

        this._updateLink(this.get());

        this.observe(function(colors) { self._updateLink(colors); });

        this.chainElements.push(this.link);

        this.link.observeClick(function() {
            if (self.active) {
                self.close();
            } else if (onclick()) {
                var pos = self.link.getAbsolutePosition();
                pos.y += self.link.dom.offsetHeight;
                if (self.alignRight){
                    pos.x += self.link.dom.offsetWidth;
                }
                self.open(pos.x + 3, pos.y + 2);
            }
        });

        return this.link;
    },
    /*
     * Sets the text and background colors
     * @param {string} textColor value (HEX value)
     * @param {string} bgColor value (HEX value)
     */
    setColors: function(textColor, bgColor) {
        this.set({
            textColor: textColor,
            bgColor: bgColor
        });
    },
    getTextColor: function() {
        return this.get().textColor;
    },
    getBgColor: function() {
        return this.get().bgColor;
    },
    _validateColor: function(color) {
        var regexp = new RegExp("^#?([a-f]|[A-F]|[0-9]){3}(([a-f]|[A-F]|[0-9]){3})?$");
        return regexp.test(color);
    },
    /*
     * Randomly returns a color among the default colors
     */
    _getRandomColors: function() {
        var rand = Math.floor(Math.random()*this.defaultColors.length);
        return this.defaultColors[rand];
    },
    /*
     * When clicking on a color update the color picker link (if there is one)
     */
    _updateLink: function(colors) {
        if (!exists(this.link)){
            return;
        }

        var cssClass = 'dropDownMenu';

        if (colors.bgColor) {
            this.link.dom.style.backgroundColor = colors.bgColor;

            if (this._colorIsDark(colors.bgColor)) {
                cssClass = 'dropDownMenuGrey';
            }
        }

        var tmp = this.link.dom.childNodes[0];
        if (colors.textColor) {
            tmp.style.color = colors.textColor;
        }
        tmp.className = 'fakeLink ' + cssClass;
    },
    /*
     * Calculates if a color should be considered as dark or light.
     * Returns true if color is dark.
     */
    _colorIsDark: function(color) {
         // Handle the case with color string having 3 chars length
         if (color.length == 4) {
             var tmp = "#";
             for (var i in color){
                 if (i !== 0) {
                     tmp += color[i] + color[i];
                 }
             }
             color = tmp;
         }
         var rgb = [
                    parseInt(color.substr(1,2), 16),
                    parseInt(color.substr(3,2), 16),
                    parseInt(color.substr(5,2), 16)
         ];

         return Math.floor((rgb[0] + rgb[1] + rgb[2]) / 3) < 128;
    }
    },
    function(chainElements, alignRight, bgColor, textColor) {
        this.triggerElement = chainElements[0];
        this.ChainedPopupWidget(chainElements, alignRight);

        // If colors not provided, select random ones
        if (!exists(textColor) || !exists(bgColor)) {
            var c = this._getRandomColors();
            textColor = c.textColor;
            bgColor = c.bgColor;
        }

        this.WatchValue({
            'textColor': textColor,
            'bgColor': bgColor
        });
    }
);
