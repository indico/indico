type("IWidget", [],
     {
         draw: function(content) {
             return content;
         },

         postDraw: function() {
         },

         _drawHeader: function() {
             return '';
         },

         disable: function() {
         },

         enable: function() {
         },

         show: function() {
         },

         hide: function() {
         }

     });

type("ListWidget", ["WatchObject", "IWidget"],
    {
        getId: function(){
            return this.id;
        },

        draw: function() {
            var self = this;

            self.domList = Html.ul(self.listCssClass);

            return this.IWidget.prototype.draw.call(
                this,
                $B(self.domList, self,
                    function(pair) {
                        return Html.li({id: self.id + '_' + pair.key},
                                       self._drawItem(pair));
                   }));
        },

        _drawItem: function(pair) {
            // Function to be overloaded by inheriting classes
            // pair is a key, value pair that can be retrieved with pair.key, pair.get()
            return '';
        }
    },

    function(listCssClass) {
        this.WatchObject();
        this.id = Html.generateId();
        this.listCssClass = listCssClass;
    }
);

type("SelectableListWidget", ["ListWidget"],
    {
        _getSelectedList: function() {
            return this.selectedList;
        },
        draw: function() {
            var self = this;

            self.domList = Html.ul(self.listCssClass);

            return this.IWidget.prototype.draw.call(
                this,
                $B(self.domList, self,
                    function(pair) {
                        var listItem = Html.li({id: self.id + '_' + pair.key}, self._drawItem(pair));
                        if (pair.get().get("unselectable") === true) {
                            listItem.dom.className += ' unselectable';
                        } else {
                            listItem.observeClick(function(){
                                if (exists(self.selectedList.get(pair.key))) {
                                    self.selectedList.set(pair.key, null);
                                    listItem.dom.className = self.unselectedCssClass;
                                } else {
                                    self.selectedList.set(pair.key, pair.get());
                                    listItem.dom.className = self.selectedCssClass;
                                }
                                self.selectedObserver(self.selectedList);
                            });
                        }
                        return listItem;
                   }));
        },
        _drawItem: function(pair) {
            // Function to be overloaded by inheriting classes
            // pair is a key, value pair that can be retrieved with pair.key, pair.get()
            return '';
        }
    },
    function (selectedObserver, listCssClass, selectedCssClass, unselectedCssClass) {
        this.selectedList = $O();
        this.selectedObserver = selectedObserver;
        if (exists (selectedCssClass)) {
            this.selectedCssClass = selectedCssClass;
        } else {
            this.selectedCssClass = "selectedListItem";
        }
        if (exists (unselectedCssClass)) {
            this.unselectedCssClass = unselectedCssClass;
        } else {
            this.unselectedCssClass = "unselectedListItem";
        }
        this.ListWidget(listCssClass);
    }
);

type("TabWidget", ["IWidget"],{
    _titleTemplate: function(text) {
        return text;
    },

    enableTab: function(index) {
        this.tabs[index].dom.style.display = 'inline';
    },

    disableTab: function(index) {
        this.tabs[index].dom.style.display = 'none';
    },

    enable: function() {
        this.disableOverlay.dom.style.display = 'none';
    },

    disable: function() {
        this.disableOverlay.dom.style.display = 'block';
    },

    _drawContent: function() {

        var self = this;

        try {

            each(this.optionDict,
                 function(value, key) {
                     if (key == self.selected.get()) {
                         value.dom.style.display = 'block';
                     } else {
                         value.dom.style.display = 'none';
                     }
                 });

        } catch(e) {
            if (e == "stopDrawing") {
                // Otherwise stop drawing
            }
        }
    },

    draw: function(dataRetrievalFunc) {
        var self = this;

        this.tabList = $B(Html.ul("tabList"),
                          this.options,
                          function(value) {
                              var liItem = Html.li(
                                  value==self.selected.get() ? "tabSelected" : "tabUnselected",
                                  Html.span({}, self._titleTemplate(value))
                              );
                              liItem.observeClick(function() {
                                  self.selected.set(value);
                              });
                              liItem.observeEvent('mouseover', function() {
                                  liItem.setStyle('backgroundPosition', '0 0px');
                              });
                              liItem.observeEvent('mouseout', function() {
                                  liItem.setStyle('backgroundPosition', '0 -30px');
                              });

                              self.selected.observe(function(selValue) {
                                  liItem.dom.className = value==selValue ? "tabSelected" : "tabUnselected";
                              });

                              self.tabs.push(liItem);

                              return liItem;
                          });
        var arrow, bg;

        arrow = Html.div({className: 'tabScrollArrow', style: {backgroundPosition: '0 -30px'}});
        bg = Html.div({className: 'tabScrollArrowBg'}, arrow);
        this.scrollArrows.right = [bg, arrow];

        arrow = Html.div({className: 'tabScrollArrow', style: {backgroundPosition: '0 -15px'}});
        bg = Html.div({className: 'tabScrollArrowBg'}, arrow);
        this.scrollArrows.left = [bg, arrow];

        this.scrollArrows.left[0].observeClick(function(event) { self.scrollLeft(); });
        this.scrollArrows.right[0].observeClick(function(event) { self.scrollRight(); });

        // Mouseover / mouseout event for changing background
        this.scrollArrows.left[0].observeEvent('mouseover', function() {
            if (!self.scrollArrowStates.left) {
                return;
            }
            self.scrollArrows.left[0].dom.style.backgroundPosition = '0 -75px';
        });
        this.scrollArrows.left[0].observeEvent('mouseout', function() {
            if (!self.scrollArrowStates.left) {
                return;
            }
            self.scrollArrows.left[0].dom.style.backgroundPosition = '0 -60px';
        });
        this.scrollArrows.right[0].observeEvent('mouseover', function() {
            if (!self.scrollArrowStates.right) {
                return;
            }
            self.scrollArrows.right[0].dom.style.backgroundPosition = '0 -75px';
        });
        this.scrollArrows.right[0].observeEvent('mouseout', function() {
            if (!self.scrollArrowStates.right) {
                return;
            }
            self.scrollArrows.right[0].dom.style.backgroundPosition = '0 -60px';
        });


        var extraButtons = "";
        // Add any extra buttons displayed under the tabs
        if (this.extraButtons.length) {
            extraButtons = Html.div('tabExtraButtons');
        }
        each(this.extraButtons, function(btn, index) {
            var extraCSSClass = '';
            if (index === 0) {
                extraCSSClass = "buttonContainerLeft";
            } else if (index == self.extraButtons.length-1) {
                extraCSSClass = "buttonContainerRight";
            }
            var btnContainer = Html.div('buttonContainer ' + extraCSSClass, btn.btn);
            extraButtons.append(btnContainer);
            btnContainer.observeClick(function() {btn.onclick(btnContainer);});
        });


        // this piece of code is sensitive to exceptions
        // coming from the drawing functions (for LookupTabWidget)
        if(dataRetrievalFunc) {
            dataRetrievalFunc.call(this);
        } else {
            each(this.optionDict,
                 function(value, key) {
                     self.canvas.append(value);
                 });
        }

        this._drawContent();

        var wrapperStyle = this.width?{width: this.width}:{};

        this.container = this.IWidget.prototype.draw.call(
            this,
            Html.div({style: wrapperStyle},
                     Html.div({className: "tabListContainer", style: {position: 'relative'}}, this.scrollArrows.left[0], this.scrollArrows.right[0], this.tabList,
                              Html.div('tabGradient', extraButtons/*,
                                       Html.div({className: 'tabBorderGradient', style: {cssFloat: 'left'}}),
                                       Html.div({className: 'tabBorderGradient', style: {cssFloat: 'right'}})*/)
                             ),
                     Html.div({style: {marginTop: pixels(10),
                                       width: self.width ? self.width : 'auto',
                                       minHeight: self.height ? pixels(self.height) : 'auto' }},
                              this.canvas),
                     this.disableOverlay));

        return this.container;
    },

    postDraw: function() {
        var self = this;

        // If no tabs exist just return
        if (this.tabs.length === 0 || !this.checkTabOverflow()) {
            return;
        }

        this.tabList.dom.style.paddingLeft = "35px";
        this.tabList.dom.style.paddingRight = "35px";

        // Iterate and hide all tabs that don't fit
        for(var i = this.tabs.length-1; i > 0; i--) {
            if (self.checkTabOverflow()) {
                this.tabs[i].dom.style.display = 'none';
            } else {
                self.rightTabIndex = i;
                break;
            }
        }

        this.scrollArrows.right[0].dom.style.left = pixels(this.container.dom.clientWidth - 17);

        // Initially allow scroll right but not left
        this.setScrollArrowState('right', true);
        this.setScrollArrowState('left', false);
    },

    checkTabOverflow: function(tab) {
        // some magic numbers used... it would be great if a better solution
        // was possible
        return (this.tabList.dom.offsetHeight > (Browser.IE?33:30));
    },

    scrollRight: function() {
        if (!this.scrollArrowStates.right) {
            return;
        }

        var rightTab = this.tabs[this.rightTabIndex];
        var nextRightTab = this.tabs[this.rightTabIndex+1];

        this.rightTabIndex++;

        rightTab.dom.style.marginRight = '';
        nextRightTab.dom.style.display = 'inline';

        // Hide as many tab as needed to the left to make the new tab to the right fit
        for (var i = this.leftTabIndex; i < this.tabs.length-1 && this.checkTabOverflow(); i++) {
            this.tabs[i].dom.style.display = 'none';
            this.tabs[i].dom.style.marginLeft = '';
            this.leftTabIndex++;
        }

        // Add as many tabs as possible to the right
        for (i = this.rightTabIndex+1; i < this.tabs.length; i++) {
            this.tabs[i].dom.style.display = 'inline';
            this.tabs[i-1].dom.style.marginRight = '';
            // If overflow, revert the changes
            if (this.checkTabOverflow()) {
                this.tabs[i].dom.style.display = 'none';
                this.tabs[i].dom.style.marginRight = '';
                break;
            } else {
                this.rightTabIndex++;
            }
        }


        // Acvtivate/inactivate the arrows accordingly
        this.setScrollArrowState('left', true);
        if (this.rightTabIndex == this.tabs.length-1) {
            this.setScrollArrowState('right', false);
        }
    },

    scrollLeft: function() {
        if (!this.scrollArrowStates.left) {
            return;
        }

        var leftTab = this.tabs[this.leftTabIndex];
        var prevLeftTab = this.tabs[this.leftTabIndex -1];

        this.leftTabIndex--;

        leftTab.dom.style.marginLeft = '';
        prevLeftTab.dom.style.display = 'inline';

        // Hide as many tab as needed to the right to make the new tab to the left fit
        for (var i = this.rightTabIndex; i >= 0  && this.checkTabOverflow(); i--) {
            this.tabs[i].dom.style.display = 'none';
            this.tabs[i].dom.style.marginRight = '';
            this.rightTabIndex--;
        }

        // Add as many tabs as possible to the left
        for (i = this.leftTabIndex-1; i >= 0; i--) {
            this.tabs[i].dom.style.display = 'inline';
            this.tabs[i+1].dom.style.marginLeft = '';
            // If overflow, revert the changes
            if (this.checkTabOverflow()) {
                this.tabs[i].dom.style.display = 'none';
                this.tabs[i].dom.style.marginLeft = '';
                break;
            }
            else {
                this.leftTabIndex--;
            }
        }

        // Acvtivate/inactivate the arrows accordingly
        this.setScrollArrowState('right', true);
        if (this.leftTabIndex < 1) {
            this.setScrollArrowState('left', false);
        }
    },

    setScrollArrowState: function(direction, active) {
        var bg = this.scrollArrows[direction][0];
        var arrow = this.scrollArrows[direction][1];
        this.scrollArrowStates[direction] = active;

        if (active) {
            arrow.dom.style.backgroundPosition = '0 -' + pixels(direction == 'right' ? 0 : 15);
            arrow.dom.style.borderColor = '#999999';
            bg.dom.style.backgroundPosition = '0 -60px';
            bg.dom.style.cursor = 'pointer';
        } else {
            arrow.dom.style.backgroundPosition = '0 -' + pixels(direction == 'right' ? 30 : 45);
            arrow.dom.style.borderColor = '#D5D5D5';
            bg.dom.style.backgroundPosition = '0 -90px';
            bg.dom.style.cursor = '';
        }
        // Make sure arrow is visible
        bg.dom.style.display = 'block';
    },

    /**
     * Returns the string with the title of the currently selected tab
     */
    getSelectedTab: function() {
        return this.selected.get();
    },

    /**
     * Changed the currently selected tab
     * @param {string} newSelectedTab The name of the new tab to be selected
     */
    setSelectedTab: function(newSelectedTab){
        this.selected.set(newSelectedTab);
    },

    initializeDisableOverlay: function() {
         this.disableOverlay = Html.div({
             style: {
                 display: 'none',
                 background: 'white',
                 opacity: '0.7',
                 height: '50px',
                 width: '100%',
                 position: 'absolute',
                 top: '0', left: '0',
                 filter: 'alpha(opacity=70)'
             }});
    }

},

     function(options, width, height, initialSelection, extraButtons, canvas) {

         var self = this;

         this.width = exists(width) ? ((typeof(width)=='string' && width.indexOf('%') >= 0) ? width : pixels(width)) : width;

         this.height = height;
         this.tabs = [];
         this.leftTabIndex = 0;
         this.rightTabIndex = 0;
         this.scrollArrows = {};
         this.scrollArrowStates = {};
         this.extraButtons = any(extraButtons, []);
         this.canvas = canvas || Html.div('canvas');

         if (!exists(initialSelection)) {
             initialSelection = options[0][0];
         }

         this.options = new WatchList();

         //replace with appropriate method, when ready
         $L(options).each(function(pair) {
             var value = pair[1];
             var key = pair[0];

             self.options.append(key);
         });

         this.optionDict = {};
         each(options, function(item) {
             self.optionDict[item[0]] = item[1];
         });

         this.selected = new WatchValue();

         this.selected.observe(function(value) {
             self._drawContent();
         });

         this.selected.set(initialSelection);

         this.initializeDisableOverlay();
     }
    );

type("LookupTabWidget", ["TabWidget"],
     {
         _drawContent: function() {
             var self = this;

             try {
                 this.canvas.set(this.optionDict[self.selected.get()]());

             } catch(e) {
                 if (e == "stopDrawing") {
                     // Otherwise stop drawing
                 }
             }
         },

         draw: function() {
             return this.TabWidget.prototype.draw.call(
                 this,
                 function() {
                     this.canvas.set(Html.div({}));
                 });
         }
     },

     function(options, width, height, initialSelection, extraButtons, canvas) {
         this.TabWidget(options, width, height, initialSelection, extraButtons, canvas);
     }

    );

type("RemoteWidget", [],
     {

         _error: function(error) {
            IndicoUI.Dialogs.Util.error(error);
         },

         run: function(content) {
             var self = this;
             var canvas = Html.div({});

             self.source.state.observe(function(value) {
                 if (value == SourceState.Loaded) {
                     canvas.set(self.drawContent(content));
                 }else if(value == SourceState.Committing){
                    self.runIndicator(canvas);
                 } else if (value == SourceState.Error) {
                     self._error(self.source.error.get());
                 }
             });
             return canvas;
         },

         draw: function(content) {
             var canvas = this.run(content);
             this.runIndicator(canvas);
             return canvas;
         },

         runIndicator: function(canvas) {
             if (!this.noIndicator) {
                 canvas.set(progressIndicator(false, true));
             }
         }
     },
     function(method, args, noIndicator) {
         this.noIndicator = noIndicator;
         this.source = indicoSource(method, args);
     });

type("RemoteListWidget", ["ListWidget", "RemoteWidget"], {

    draw: function() {
        return this.RemoteWidget.prototype.draw.call(this);
    },

    getList: function() {
        return this.source;
    },

    _addElement: function(element) {
        // overloaded if greater degree of control required
        this.add(element);
    },

    /**
     * drawContent is a method that is called from RemoteWidget when the source changes.
     *
     */
    drawContent: function() {
        var self = this;
        this.clear();
        each($L(this.getList()), function(elem){
                self._addElement(elem);
                });
        return this.ListWidget.prototype.draw.call(this);
    }

    },
    function(listCssClass, method, args, noIndicator) {
        this.ListWidget(listCssClass);
        this.RemoteWidget(method, args, noIndicator);
    });

type("PreloadedWidget", ["IWidget"],
     {
         draw: function() {
             var canvas = Html.span({}, 'loading...');
             var count = 0;

             var self = this;

             var checkNow = function() {
                 if (count == self.waitingList.length) {
                     canvas.set(self.drawContent());
                 }
             };

             each(this.waitingList,
                  function(remoteWidget) {
                      remoteWidget.ready.observe(function(value) {
                          if (value) {
                              count++;
                              checkNow();
                          }
                      });
                  });

             return canvas;
         }
     },
     function(waitingList) {
         this.waitingList = waitingList;
     });

progressIndicator = function(small, center) {
    var htmlTag = small?Html.span:Html.div;
    return htmlTag(center?{style:{textAlign: 'center'}}:{},Html.img({src: imageSrc(small?"loading":"ui_loading"), alt: "Loading..."
}));
};

type("ServiceWidget", ["IWidget"],
     {
         _error: function(error) {
             IndicoUI.Dialogs.Util.error(error);
         },

         request: function(extraArgs) {
             var self = this;
             var args = extend(clone(this.args), extraArgs);

             var killProgress = IndicoUI.Dialogs.Util.progress();

             jsonRpc(Indico.Urls.JsonRpcService, this.method, args,
                     function(response,error) {
                         if(exists(error)) {
                             killProgress();
                             self._error(error);
                         } else {
                             self._success(response);
                             killProgress();
                         }
                     }
                    );
         }
     },

     function(endPoint, method, args) {
         this.endPoint = endPoint;
         this.method = method;
         this.args = args;
         this.IWidget();
     }
    );

type("PopupWidget", [], {
    draw: function(content, x, y, styles) {
        var self = this;

        this.x = x;
        this.y = y;

        /*
         * Create canvas if not already created.
         * Used to avoid errors for classes that don't
         * call the constructor.
         */
        if(!exists(this.canvas)) {
            this.canvas = Html.div();
        }

        styles = any(styles, {
            // If the canvas has been set to fixed position don't change it
            position: this.canvas.dom.style.position == 'fixed' ? 'fixed' : 'absolute',
            left: pixels(x),
            top: pixels(y)
        });

        each(styles, function(value, key) {
                self.canvas.setStyle(key, value);
        });
        this.canvas.setContent(content);

        IndicoUI.assignLayerLevel(this.canvas);

        return this.canvas;
    },

    /**
     * Opens the PopupWidget
     * @param {Integer} x The horizontal position of the top left corner.
     * @param {Integer} y The vertical position of the top left corner.
     */
    open: function(x, y) {
        $E(document.body).append(this.draw(x,y));
        this.isopen = true;
        this.postDraw();
    },

    isOpen: function() {
        return this.isopen;
    },

    postDraw: function() {
        if (Browser.IE) {
            this.canvas.dom.style.display = '';
        }
    },

    openRelative: function(x, y) {
        var iebody=(document.compatMode && document.compatMode != "BackCompat")? document.documentElement : document.body;
        var dsocleft=document.all? iebody.scrollLeft : pageXOffset;
        var dsoctop=document.all? iebody.scrollTop : pageYOffset;
        this.open(x+dsocleft, y+dsoctop);
    },

    getCanvas: function() {
        return this.canvas;
    },

    setFixedPosition: function(fixed) {
        fixed = any(fixed, true);
        this.canvas.dom.style.position = fixed ? 'fixed' : 'absolute';
    },

    close: function(e) {
        var self = this;

        IndicoUI.unAssignLayerLevel(this.canvas);

        /*
         * IE problem. If the close is triggered by en event and this.canvas
         * is remvoved from the dom tree then the event wont propagate.
         * This is fixed by hiding the element and removing it with a timeout so that
         * there is time enough for the event to be handled.
         */
        if (Browser.IE) {
            this.canvas.dom.style.display = 'none';
            setTimeout(function() {
                $E(document.body).remove(self.canvas);
            }, 500);
        } else {
            $E(document.body).remove(self.canvas);
        }

        this.isopen = false;
    }
    },
    function(styleData) {
        this.canvas = Html.div({style: styleData}||{});
    }
);

type("HistoryListener", [],
     {
         _addToHistory: function(hash) {
             // Add hash to history
             if (this.historyBroker) {
                 this.historyBroker.setUserAction(hash);
             }
         },

         registerHistoryBroker: function(broker) {
             this.historyBroker = broker;
         },

         notifyHistoryChange: function(hash) {
             this._retrieveHistoryState(hash);
         }
     },
     function() {

     });

type("ErrorAware", [],
     {
         _setElementErrorState: function(element, text) {
             this._stopErrorList = IndicoUtil.markInvalidField(element, text)[1];
         },

         setError: function(text) {
             if (!text) {
                 // everything back to normal
                 if (this._stopErrorList){

                     each(this._stopErrorList,
                          function(elem) {
                              elem();
                          });

                     this._inError = false;
                     this._stopErrorList = [];
                 }
             } else {
                 this._setErrorState(text);
                 this._inError = true;
             }
             return this._stopErrorList;
         },

         inError: function() {
             return this._inError;
         },

         askForErrorCheck: function() {
             var errorState = this._checkErrorState();

             if (errorState) {
                 // if we're already in error state,
                 // no need to do anything

                 if (!this._inError) {
                     // otherwise, we have to set it
                     this.setError(errorState);
                 }
                 return errorState;
             } else {
                 this.setError(null);
                 return null;
             }
         }
     },
     function(parameterManager) {
         this.parameterManager = parameterManager;

         var self = this;

         parameterManager.add(self, null, null,
                              function(){
                                  return self.askForErrorCheck();
                              });
     });
