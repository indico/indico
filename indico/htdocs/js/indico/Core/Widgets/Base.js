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

var addedWebkitJqueryFixDiv = false;

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

/**
 * Base class for widgets that store internally a list and want to represent each item with a template;
 * the list will be a <ul> and the items a <li> each, bound to the item data.
 *
 * The <ul> will have a random DOM id and each <li> will also have a DOM id: the <ul>'s id + _ + item_key.
 *
 * Inherits from WatchObject: each item will have a key and a value (the item data).
 * When adding a new item, it will always appear last in the DOM.
 * To add / remove items use the corresponding WatchObject methods: "set(key, item)" to add, or "set(key, null)" to remove.
 *
 * This class also has a "setMessage" method, which will delete all the items in the <ul> and display the message inside.
 *
 * Inheriting classes will have to implement the _drawItem method.
 *
 * @param {String} listCssClass CSS class for the <ul> element.
 * @param {function} mouseoverObserver A function that will be called when the user hovers the mouse over one of the <li>.
 *                                     It will be called with 4 arguments:
 *                                     1. true / false. true for mouseover, false for mouseout.
 *                                     2. a "pair" object representing the item corresponding to the <li>.
 *                                     pair.key will be the item's key and pair.get() the item's data.
 *                                     3. the <li> XElement that received the event
 *                                     4. the event object
 *
 */
type("EnumWidget", ["WatchObject", "IWidget"],
    {
        /**
         * The DOM id of the <ul> element, chosen randomly at construction.
         */
        getId: function(){
            return this.id;
        },

        /**
         * We cannot call this function "clear" because
         * WatchObject's "clear" is defined in the WatchObject constructor
         * and would squash our function.
         */
        clearList: function() {
            var self = this;
            self.message = null;
            self.clear(); // this gets rid of the <li> representing (key,values)
            self.domList.clear(); //this gets rid of eventual messages
        },

        /*
         * Overloaded
         */
        _getHeader: function() {
            return null;
        },

        /**
         * Sets a message inside the list.
         * This will delete all the internal data.
         */
        setMessage: function(message) {
            this.clearList();
            this.message = message;
            this.domList.append(Html.li('listMessage', message));
        },

        draw: function() {
            var self = this;
            var returnedDom = $B(self.domList, self, function(pair) {
                var listItem =  self._iteratingElement({id: self.id + '_' + pair.key, pair: pair}, self._drawItem(pair));
                if (exists(self.mouseoverObserver)) {
                    listItem.observeEvent('mouseover', function(event){
                        self.mouseoverObserver(true, pair, listItem, event);
                    });
                    listItem.observeEvent('mouseout', function(event){
                        self.mouseoverObserver(false, pair, listItem, event);
                    });
                }

                self._postDraw(pair);
                return listItem;
            });

            // Optional header
            var header = self._getHeader();
            if (header) {
                self.domList.insert(header);
            }

            if (exists(this.message)) {
                this.domList.append(self._iteratingElement('listMessage', this.message));
            }
            return this.IWidget.prototype.draw.call(this, returnedDom);
        },

        _postDraw: function(pair){
            return '';
        },

        _drawItem: function(pair) {
            // Function to be overloaded by inheriting classes
            // pair is a key, value pair that can be retrieved with pair.key, pair.get()
            return '';
        }
    },

    /**
     * Constructor
     */
    function(listCssClass, mouseoverObserver) {
        this.WatchObject();
        this.id = Html.generateId();
        this.domList = this._containerElement({id: this.id, className: listCssClass});
        this.listCssClass = listCssClass;
        this.mouseoverObserver = mouseoverObserver;
    }
);

type("TableWidgetMixin", [],
     {
         _iteratingElement: function() {
             return Html.tr.apply(this, arguments);
         },

         _containerElement: function() {
             return Html.table.apply(this, arguments);
         }
     });

type("ListWidgetMixin", [],
     {
        _iteratingElement: function() {
            return Html.li.apply(this, arguments);
        },

        _containerElement: function() {
            return Html.ul.apply(this, arguments);
        }
     });

declareMixin("ListWidget", "EnumWidget", ["ListWidgetMixin"]);
declareMixin("TableWidget", "EnumWidget", ["TableWidgetMixin"]);

/**
 * Base class which adds selection capability to ListWidget.
 * See first the documentation of ListWidget.
 *
 * @param {function} selectedObserver Function that will be called when an item is selected / unselected.
 *                                    It will be passed the list of currently selected items, as a WatchObject
 *                                    similar to the internal WatchObject that holds all the items.
 *
 * @param {Boolean} onlyOne false by default. If true, selecting an item will deselect a previously selected item.
 *
 * @param {String} listCssClass see ListWidget doc.
 * @param {String} selectedCssClass CSS class that will be added to the <li> if they are selected.
 * @param {String} unselectedCssClass CSS class that will be added to the <li> if they are unselected.
 *
 * @param {function} mouseoverObserver see ListWidget doc.
 */
type("SelectableListWidget", ["ListWidget"],
    {
        getSelectedList: function() {
            return this.selectedList;
        },

        clearSelection: function() {
            var self = this;
            each(self.domList, function(listItem) {
                if (listItem.dom.className.search(self.selectedCssClass) >= 0) {
                    listItem.dom.className = listItem.dom.className.replace(self.selectedCssClass, self.unselectedCssClass);
                }
            });
            this.selectedList.clear();
        },

        selectAll: function() {
            var self = this;
            each(self.domList, function(listItem) {
                listItem.dom.className = self.selectedCssClass;
            });
            each(self, function(value, key) {
                self.selectedList.set(key, value);
            });
            if (exists(self.selectedObserver)) {
                self.selectedObserver(self.selectedList);
            }
        },

        /**
         * We cannot call this function "clear" because
         * WatchObject's "clear" is defined in the WatchObject constructor
         * and would squash our function.
         */
        clearList: function() {
            this.clearSelection();
            this.ListWidget.prototype.clearList.call(this);
        },

        /**
         * Sets a message inside the list.
         * This will delete all the internal data.
         */
        setMessage: function(message) {
            this.clearSelection();
            this.ListWidget.prototype.setMessage.call(this, message);
        },

        selectItem: function(listItem, pair){
            var self = this;
            if (exists(self.selectedList.get(pair.key))) {
                self.selectedList.set(pair.key, null);
                listItem.dom.className = self.unselectedCssClass;
            } else {
                if (self.onlyOne) {
                    self.clearSelection();
                }
                self.selectedList.set(pair.key, pair.get());
                listItem.dom.className = self.selectedCssClass;
            }

            if (exists(self.selectedObserver)) {
                self.selectedObserver(self.selectedList);
            }
        },

        getReturnedDOM: function(self) {
            var dom = $B(self.domList, self,

                function(pair) {
                    var listItem = Html.li({id: self.id + '_' + pair.key}, self._drawItem(pair));
                    if (pair.get().get("unselectable") === true) {
                        listItem.dom.className += ' unselectable';

                    } else {
                        listItem.observeClick(function(event){self.selectItem(listItem, pair)});
                    }
                    if (exists(self.mouseoverObserver)) {
                        listItem.observeEvent('mouseover', function(event){
                            self.mouseoverObserver(true, pair, listItem, event);
                        });
                        listItem.observeEvent('mouseout', function(event){
                            self.mouseoverObserver(false, pair, listItem, event);
                        });
                    }
                    return listItem;
               });

            if (exists(this.message)) {
                this.domList.append(Html.li('listMessage', this.message));
            }

            return dom;
        },

        draw: function() {
            var self = this;
            var returnedDom = self.getReturnedDOM(self);

            return this.IWidget.prototype.draw.call(this, returnedDom);
        },
        _drawItem: function(pair) {
            // Function to be overloaded by inheriting classes
            // pair is a key, value pair that can be retrieved with pair.key, pair.get()
            return '';
        }
    },
    function (selectedObserver, onlyOne, listCssClass, selectedCssClass, unselectedCssClass, mouseoverObserver) {
        this.selectedList = $O();
        this.selectedObserver = selectedObserver;
        this.onlyOne = any(onlyOne, false);
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
        this.ListWidget(listCssClass, mouseoverObserver);
    }
);

/**
 * Extension to SelectableListWidget to provide lazy-loading-esque functionality,
 * by requesting an Indico API method (and its args) to be passed as an arguement
 * which allows the contents of this list to be extended by an interval (set
 * either at instantiation or during execution via setInteval(int). For situations
 * whereby it is anticipated that a lot of data may be returned to do so
 * gradually.
 */
type("SelectableDynamicListWidgetBase", ["SelectableListWidget"],
    {
        interval: null,
        offset: 0,
        itemsBuffer: [],
        tmpBuffer: null,
        APIMethod: null,
        APIArgs: null,
        ajaxPending: null,
        complete: false,

        draw: function() {
            var self = this;
            var returnedDom = self.getReturnedDOM(self);

            return [this.SelectableListWidget.prototype.draw.call(this, returnedDom),
                    self.getListActions()];
        },

        /**
         * Sets internal flag to denote that all records have been retrieved,
         * do not try to perform any more server calls.
         */
        _setComplete: function() {
            var self = this;
            self.complete = true;
        },

        /**
         * Returns boolean if all records retrieved.
         */
        _isComplete: function() {
            return this.complete;
        },

        /**
         * To be implemented as per requirement, for progress indicators etc.
         */
        _waitHandler: function() {
            var self = this;
            self.progress.dom.style.display = 'block';
        },

        /**
         * Append another subset of values of size k = this.interval to the
         * existing buffer of results.
         */
        loadInterval: function() {
            var self = this;
            var args = self.APIArgs;

            if (self._isComplete()) {
                return true;
            }

            self._waitHandler();
            args.limit = self.interval;
            args.offset = self.offset;

            self.ajaxPending = $.Deferred();
            self._performCall(args);

            $.when(self.ajaxPending).done(function() {
                self.itemsBuffer = self.itemsBuffer.concat(self.tmpBuffer);
                self._updateDraw();
            });

            return true;
        },

        /**
         * Clears the internal buffer and retrieves all the records associated
         * to the API query. May take some time to complete.
         */
        loadAll: function() {
            var self = this;
            var args = self.APIArgs;

            if (self._isComplete()) {
                return true;
            }

            self._waitHandler();
            args.limit = null;
            args.offset = self.offset;

            self.ajaxPending = $.Deferred();
            self._performCall(args);

            $.when(self.ajaxPending).done(function() {
                self.itemsBuffer = self.itemsBuffer.concat(self.tmpBuffer);
                self.clearList();
                self._setComplete();
                self._updateDraw();
            });

            return true;
        },

        /**
         * Returns true if this implementation has an active waiting object.
         */
        _hasAjaxPending: function() {
            return (self.ajaxPending !== null);
        },

        _updateOffset: function() {
            self.offset += this.getInterval();
        },

        /**
         * Set the parent object's items based on this item buffer and draw
         * the result.
         */
        _updateDraw: function() {
            var self = this;
            self.tmpBuffer = null;
            self.ajaxPending = null;
            self._updateOffset();
            self._setItems(self.itemsBuffer);
            $(self.progress.dom).hide();
            $('#sdlw-load').show();
            return self.draw();
        },

        /**
         * Returns 'Load More' and 'Load All' links with observers
         * as entries.
         */
        getListActions: function() {
            var self = this;
            var noMoreEntries = Html.span({id: 'sdlw-complete'}, self.noMoreEntriesMsg);
            var load = Html.span({id: 'sdlw-load', style: {'display': 'none'}});

            if (self._isComplete()) {
                $('div#sdlw-actions').html(noMoreEntries.get());
                $('div#sdlw-actions').attr('class', 'sdlw-complete');
                return;
            }

            var progressSpan = Html.div({id: 'sdlw-progress'}, self.progress);
            var loadMore = Html.span({
                className: 'fakeLink'},
                $T("See " + self.getInterval() + " results more"));
            var loadAll = Html.span({
                className: 'fakeLink'},
                $T("See all"));

            loadMore.observeClick(function(evt) {
                $(load.dom).hide();
                progressSpan.set(self.progress);
                self.loadInterval();
            });

            loadAll.observeClick(function(evt) {
                $(load.dom).hide();
                progressSpan.set(self.progress);
                self.loadAll();
            });

            load.append(loadMore);
            load.append(' - ');
            load.append(loadAll);

            return Html.div({id: 'sdlw-actions'}, load, progressSpan);
        },

        /**
         * Sets the interval at runtime, whether or not already set at object
         * instantiation.
         */
        setInterval: function(interval) {
            this.interval = interval;
        },

        /**
         * Returns integer value of iteration for stepping through results.
         */
        getInterval: function() {
            return this.interval;
        },

        /**
         * To be overloaded - propagate structures accordingly
         */
        _performCall: function(args) {
            var errorMsg = "_performCall not overloaded in subclass.";
            IndicoUtil.errorReport(errorMsg);
            return false;
        },

        /**
         * To be overloaded - inheriting object to iterate data and apply set()
         * to each.
         */
        _setItems: function(items) {
            var errorMsg = "_setItems not overloaded in subclass.";
            IndicoUtil.errorReport(errorMsg);
            return false;
        }
    },

    function (selectedObserver, onlyOne, listCssClass, selectedCssClass,
              unselectedCssClass, mouseoverObserver, SDLParams, noMoreEntriesMsg) {

        var self = this;
        var defaultInterval = 15;

        self.progress = progressIndicator(false, true);
        self.APIMethod = SDLParams.method;
        self.APIArgs = SDLParams.args;
        self.interval = (self.APIArgs.limit === undefined)
                        ? defaultInterval
                        : self.APIArgs.limit;

        self.noMoreEntriesMsg = any(noMoreEntriesMsg, $T('No more to load'));

        self.SelectableListWidget(selectedObserver, onlyOne, listCssClass,
                selectedCssClass, unselectedCssClass, mouseoverObserver, noMoreEntriesMsg);
    }
);


type("SelectableDynamicListWidget", ["SelectableDynamicListWidgetBase"],
    {

        getList: function() {
            return this.getSelectedList();
        },

         /**
         * Prepare the items for the format required later by the form.
         */

        _prepareItems: function(itemsRaw) {
            var items = {};

            each(itemsRaw, function(item) {
                items[item.name] = item;
            });

            return items;
        },

        _setItems: function(itemsRaw) {
            var self = this;
            var items = self._prepareItems(itemsRaw);
            var ks = keys(items);

            for (k in ks) {
                this.set(k, $O(items[ks[k]]));
            }
        },

        _extractResult: function(result) {
            return result;
        },

        _performCall: function(args) {
            var self = this;

            indicoRequest(self.APIMethod, args, function(result, error) {
                if (!error) {
                    self.tmpBuffer = self._extractResult(result);

                    if (self.tmpBuffer.length < self.getInterval()) {
                        self._setComplete();
                    }

                    if (self._hasAjaxPending()) {
                        self.ajaxPending.resolve();
                    }
                } else {
                    IndicoUtil.errorReport(error);
                }
            });

            return self.tmpBuffer;
        }
    },

    function (observer, method, args, listCssClass, onlyOne, noMoreEntriesMsg) {
        var self = this;
        this.selected = new WatchList();

        var SDLWidgetParams = {
                method: method,
                args: args
        };

        this.SelectableDynamicListWidgetBase(observer, onlyOne, listCssClass, null,
                                         null, null, SDLWidgetParams, noMoreEntriesMsg);

        self.loadInterval();

    }
);

type("JTabWidget", ["IWidget"], {
    _addTab: function(label, content, data) {
        var id = _.uniqueId('x-tab-');
        $(content).css('display', '').find('script').remove();
        var container = $('<div/>', { id: id }).data(data || {}).html(content);
        var navLink = $('<a>', {
            href: '#' + id,
            text: this._titleTemplate(label)
        });
        this.widget.append(container);
        this.widget.find('.ui-tabs-nav').append($('<li>').append(navLink));
        this.widget.tabs('refresh');
        if(this.widget.tabs('option', 'active') === false) {
            // focus first tab
            this.widget.tabs('option', 'active', 0);
        }
    },
    _titleTemplate: function(text) {
        return text;
    },
    draw: function() {
        var self = this;
        // We are going to be visible right after this function, so let's update the scroll buttons when size information is available
        _.defer(function() {
            self._updateScrollButtons();
            // Also call the on draw functions here
            $.each(self._onDraw, function(i, func) {
                func();
            });
            self._onDraw = [];
        });
        return self.widget[0];
    },
    enable: function() {
        this.widget.tabs('enable');
        for(var i = 0, num = this.widget.data('ui-tabs').anchors.length; i < num; i++) {
            this.enableTab(i);
        }
        if(this.scrollable) {
            this._updateScrollButtons();
        }
    },
    disable: function() {
        this.widget.tabs('disable');
        for(var i = 0, num = this.widget.data('ui-tabs').anchors.length; i < num; i++) {
            this.disableTab(i);
        }
        if(this.scrollable) {
            this.scrollButtons.children().addClass('ui-state-disabled');
        }
    },
    enableTab: function(index) {
        this.widget.tabs('enable', index);
    },
    disableTab: function(index) {
        this.widget.tabs('disable', index);
    },
    getLabel: function(index) {
        return $('.ui-tabs-nav > li', this.widget).eq(index);
    },
    getTabIndex: function(label) {
        var self = this;
        return $('.ui-tabs-nav > li', self.widget).filter(function() {
            return $(this).text() == self._titleTemplate(label);
        }).eq(0).index();
    },
    getSelectedIndex: function() {
        return this.widget.tabs('option', 'active');
    },
    getSelectedTab: function() {
        return this.getLabel(this.getSelectedIndex());
    },
    setSelectedTab: function(labelOrIndex){
        var idx = _.isNumber(labelOrIndex) ? labelOrIndex : this.getTabIndex(labelOrIndex);
        this.widget.tabs('option', 'active', idx);
        this.scrollToTab(idx, true);
    },
    getSelectedPanel: function() {
        var index = this.widget.tabs('option', 'active');
        return $('> div.ui-tabs-panel', this.widget).eq(index);
    },
    heightToTallestTab: function() {
        var maxHeight = 0;
        var panel = $('> div.ui-tabs-panel', this.widget);
        panel.each(function() {
            maxHeight = Math.max(maxHeight, $(this).height());
        });
        // Chrome sometimes shows scrollbars until a tab change if we don't wait a moment with applying the height
        _.defer(function() {
            panel.height(maxHeight);
        });
    },
    makeScrollable: function() {
        var self = this;
        if(self.scrollable) {
            return;
        }
        self.scrollable = true;
        var nav = $('> .ui-tabs-nav', self.widget); // the ul containing the tabs
        nav.css('padding', 0);
        // by wrapping the div and disabling floating for tabs we ensure tabs do not wrap into another line
        nav.wrap($('<div/>').css({
            whiteSpace: 'nowrap',
            overflow: 'hidden'
        }));
        nav.find('> li').css({
            'display': 'block',
            'float': 'left'
        });
        // save some space for the scroll buttons
        nav.css({
            marginLeft: '17px',
            marginRight: '15px'
        });

        var arrowsTopMargin = '4px';
        var arrowsCommonCss = {
            cursor: 'pointer',
            zIndex: 99,
            position: 'absolute',
            top: '1px',
            height: '26px'
        };

        self.scrollOffset = 0; // how many tabs did the user scroll to the right
        // Create buttons to scroll left/right
        self.scrollButtons = $('<div/>').disableSelection().css({
            position: 'relative',
            zIndex: 100
        });
        $('<span/>')
            .disableSelection()
            .attr('title', $T('Previous tab'))
            .css(arrowsCommonCss)
            .css('left', 0)
            .addClass('ui-state-active ui-corner-tl ui-corner-bl')
            .append($('<span/>').disableSelection().addClass('ui-icon ui-icon-carat-1-w').html($T('Previous tab')).css('marginTop', arrowsTopMargin))
            .click(function() {
                if($(this).hasClass('ui-state-disabled')) {
                    return;
                }
                self.scrollToTab(Math.max(0, self.scrollOffset - 1));
            }).appendTo(self.scrollButtons);
        $('<span/>')
            .disableSelection()
            .attr('title', $T('Next tab'))
            .css(arrowsCommonCss)
            .css('right', 0)
            .addClass('ui-state-active ui-corner-tr ui-corner-br')
            .append($('<span/>').addClass('ui-icon ui-icon-carat-1-e').html($T('Next tab')).css('marginTop', arrowsTopMargin))
            .click(function() {
                if($(this).hasClass('ui-state-disabled')) {
                    return;
                }
                self.scrollToTab(Math.min(nav.find('> li').length - 1, self.scrollOffset + 1));
            }).appendTo(self.scrollButtons);
        self.scrollButtons.prependTo(self.widget);
        // Scroll to the currently selected tab
        self.scrollToTab(self.getSelectedIndex(), true);
    },
    _updateScrollButtons: function() {
        if(!this.scrollable) {
            return;
        }
        var nav = $('.ui-tabs-nav:first', this.widget);
        var visibleTabs = 0;
        var width = 0;
        var navWidth = nav.width();
        nav.find('> li:visible').each(function() {
            width += $(this).outerWidth(true);
            if(width >= navWidth) {
                return false;
            }
            visibleTabs++;
        });
        var lastElementShown = false;
        if(this.scrollOffset + visibleTabs == nav.find('> li').length) {
            lastElementShown = true;
        }
        // no prev allowed if scrolled to the far left
        this.scrollButtons.children().eq(0).toggleClass('ui-state-disabled', this.scrollOffset == 0);
        // no next allowed if last element is visible
        this.scrollButtons.children().eq(1).toggleClass('ui-state-disabled', lastElementShown);
    },
    scrollToTab: function(idx, fuzzy) {
        var self = this;
        if(!self.scrollable) {
            return;
        }
        if(fuzzy && !$('.ui-tabs-nav:first', self.widget).width()) {
            // If we want a fuzzy selection (show as many tabs as possible) and we do not have size information yet, delay everything
            self._onDraw.push(function() {
                self.scrollToTab(idx, fuzzy);
            });
            return;
        }
        else if(fuzzy && idx > 0) {
            // Yuck! Since tabs have different sizes (due to content and also selected/unselected) we need to test how far we need to scroll.
            // Would be much nicer if we could calculate it but the width is not available at all for hidden elements.
            var nav = $('.ui-tabs-nav:first', self.widget);
            if(!$.browser.msie) {
                var origIdx = idx;
                while(idx >= 0) {
                    self.scrollToTab(idx - 1); // try scrolling left 1 tab
                    if(nav.find(' > li').eq(origIdx).is(':hidden')) { // if our tab is now hidden, scroll one tab forward again and stop
                        self.scrollToTab(idx);
                        return;
                    }
                    idx--;
                }
                // if we did not break before, something probably went wrong - let's scroll to the tab directly
                self.scrollToTab(origIdx);
                return;
            }
            else {
                // In IE it's too slow. Let's use a less perfect match that is much faster though.
                var allTabs = nav.find('> li');
                var totalWidth = 0;
                $.each(allTabs, function() {
                    totalWidth += $(this).outerWidth(true);
                });
                var avgTabWidth = Math.ceil(totalWidth / allTabs.length);
                var avgVisibleTabs = Math.floor(nav.width() / avgTabWidth);
                if(idx + avgVisibleTabs >= allTabs.length) {
                    idx = allTabs.length - avgVisibleTabs + 1;
                }
            }
        }

        // Here we perform the actual "scrolling" (which is actually just hiding the "scrolled out" tabs)
        self.scrollOffset = idx;
        // show all tabs and then hide those before the visible ones
        $('.ui-tabs-nav:first > li', self.widget).show().slice(0, self.scrollOffset).hide();
        // hide the tabs after the visible ones (to ensure we don't get a "half" tab)
        var nav = $('.ui-tabs-nav:first', self.widget);
        var visibleTabs = 0;
        var width = 0;
        var updateTabsAfter = function() {
            var navWidth = nav.width();
            nav.find('> li:visible').each(function() {
                width += $(this).outerWidth(true);
                if(width >= navWidth) {
                    return false;
                }
                visibleTabs++;
            });
            $('.ui-tabs-nav:first > li', self.widget).slice(self.scrollOffset + visibleTabs).hide();
        };
        // We only have a width if the tab widget is already visible - otherwise don't do anything
        if(nav.width()) {
            updateTabsAfter();
        }
        else {
            self._onDraw.push(updateTabsAfter);
        }
        self._updateScrollButtons();
    },
    showNotification: function(index, text) {
        var label = this.getLabel(index);
        label.qtip({
            content: text,
            position: {
                my: 'bottom middle',
                at: 'top middle',
                viewport: $(window)
            },
            show: {
                event: false
            },
            hide: {
                event: 'unfocus'
            },
            style: {
                classes: 'qtip-rounded qtip-balloon',
                tip: {
                    corner: true,
                    width: 20,
                    height: 15
                }
            }
        }).qtip('show');
    },
    hideNotification: function(index) {
        var label = this.getLabel(index);
        label.qtip('destroy');
    },
    _drawExtraButtons: function() {
        // Add any extra buttons displayed under the tabs
        var container = $('<div class="tabExtraButtons"/>');
        $.each(this.extraButtons, function(i, btnData) {
            var btn = $('<div class="buttonContainer"/>').append(btnData.btn.dom || btnData.btn).click(function() {
                btnData.onclick(btn);
            });
            container.append(btn);
        });
        container.children(':first').addClass('buttonContainerLeft');
        container.children(':last').addClass('buttonContainerRight');
        this.widget.append(container);
    },
    _notifyTabChange: function() { }
}, function(tabs, width, height, initialSelection, extraButtons, canvas) {
    var self = this;
    self.scrollable = false;
    self._onDraw = [];
    self.widget = $('<div><ul/></div>');
    self.extraButtons = extraButtons || [];
    // create canvas element
    if(canvas) {
        self.canvas = $(canvas.dom || canvas);
    }
    else {
        self.canvas = $('<div/>');
    }
    self.width = exists(width) ? ((typeof(width)=='string' && width.indexOf('%') >= 0) ? width : pixels(width)) : width;
    if(self.width) {
        self.widget.width(self.width);
    }
    if(height) {
        self.widget.css('minHeight', height);
    }
    if(self.extraButtons) {
        self._drawExtraButtons();
    }
    self.widget.tabs({
        beforeActivate: function(e, ui) {
            self._notifyTabChange();
        }
    });
    // add initial tabs
    $.each(tabs, function(i, tab) {
        var content = tab[1].dom ? tab[1].dom : tab[1];
        self._addTab(tab[0], content);
    });
    if(initialSelection) {
        self.setSelectedTab(initialSelection);
    }
});

type("JLookupTabWidget", ["JTabWidget"], {
    _addTab: function(label, generator) {
        var content = '<div/>';
        this.JTabWidget.prototype._addTab.call(this, label, content, {generator: generator});
    },
    _generateContent: function(panel) {
        var container = $('> div', panel);
        var generator = $(panel).data('generator');
        try {
            var content = generator();
        } catch(e) {
            if(e == 'stopDrawing') {
                return;
            }
            throw e;
        }
        if(content.dom) {
            content = content.dom;
        }
        this.canvas.empty().append(content);
        container.empty().append(this.canvas);
    }
}, function(tabs, width, height, initialSelection, extraButtons, canvas) {
    var self = this;
    self.JTabWidget(tabs, width, height, initialSelection, extraButtons, canvas);
    self.widget.bind('tabsactivate', function(e, ui) {
        self._generateContent(ui.newPanel);
    });
    self._generateContent(self.getSelectedPanel());
});


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

    _notifyTabChange: function(from, to) {
        // to be overloaded
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
                                  self._notifyTabChange(self.selected.get(), value);
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

    heightToTallestTab: function() {
        var currentSelectedTab = this.getSelectedTab();
        var maxHeight = 0;
        for(var i = this.tabs.length-1; i >= 0; i--) {
            this.setSelectedTab(this.options.item(i));
            maxHeight = Math.max(maxHeight, this.container.dom.offsetHeight);
        }
        this.container.setStyle('height', maxHeight);
        this.setSelectedTab(currentSelectedTab);
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

         this.selected.set(initialSelection);

         this.selected.observe(function(value) {
             self._drawContent();
         });

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
                     self._stopIndicator();
                 } else if(value == SourceState.Loading || value == SourceState.Committing){
                     self._runIndicator(canvas);
                 } else if (value == SourceState.Error) {
                     self._error(self.source.error.get());
                     self._stopIndicator();
                 }
             });
             return canvas;
         },

         draw: function(content) {
             var canvas = this.run(content);
             this._runIndicator(canvas);
             return canvas;
         },

         _runIndicator: function(canvas) {
             if (!this.noIndicator) {
                 canvas.set(progressIndicator(false, true));
             }
         },

         _stopIndicator: function(canvas) {
         }


     },
     function(method, args, noIndicator) {

         this.noIndicator = noIndicator;

         // progress indicator disabled for now
         this._stopIndicator();
         this.source = indicoSource(method, args);
     });

type("RemoteEnumWidget", ["EnumWidget", "RemoteWidget"], {

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
        return this.EnumWidget.prototype.draw.call(this);
    }

    },
    function(listCssClass, method, args, noIndicator) {
        this.EnumWidget(listCssClass);
        this.RemoteWidget(method, args, noIndicator);
    });

declareMixin("RemoteListWidget", "RemoteEnumWidget", ["ListWidgetMixin"]);
declareMixin("RemoteTableWidget", "RemoteEnumWidget", ["TableWidgetMixin"]);


var progressIndicator = function(small, center) {
    var htmlTag = small ? Html.span : Html.div;
    return htmlTag(center ? {style: {textAlign: 'center'}} : {},
                   Html.img({src: imageSrc(small ? "loading" : "load_big", 'gif'), alt: "Loading..."}));
};


type("PopupWidget", [], {
    draw: function(content, x, y, styles, setWidth) {
        var self = this;

        this.x = x;
        this.y = y;

        /*
         * Create canvas if not already created.
         * Used to avoid errors for classes that don't
         * call the constructor.
         */
        if(!exists(this.canvas)) {
            this.canvas = Html.div({});
        }

        styles = any(styles, {
            // If the canvas has been set to fixed position don't change it
            position: 'absolute',
            left: pixels(x),
            top: pixels(y)
        });

        if(setWidth) {
            var width = $('body').width() - x;
            styles.width = pixels(width);
        }

        $(this.canvas.dom).css(styles).html(content.dom);

        IndicoUI.assignLayerLevel(this.canvas);

        /* This fixes an issue caused by chrome/jquery (embedded e.g. by Adblock) which
         * prevents dialogs from showing. Inserting an empty div fixes it (probably whatever
         * incorrect was still active now affects that diff instead of the dialog)
         * Related bug report: http://code.google.com/p/chromium/issues/detail?id=72568
         */
        if(!addedWebkitJqueryFixDiv && navigator.userAgent.indexOf('WebKit') != -1) {
            $('body').append('<div/>');
        }
        addedWebkitJqueryFixDiv = true; // also set to true if we do not have a webkit browser so we don't check again

        return this.canvas;
    },

    /**
     * Opens the PopupWidget
     * @param {Integer} x The horizontal position of the top left corner.
     * @param {Integer} y The vertical position of the top left corner.
     */
    open: function(x, y) {
        //$E(document.body).append(this.draw(x,y));
        var stuff = this.draw(x, y).dom;
        $('body').append(stuff);
        this.isopen = true;
        this.postDraw();
    },

    isOpen: function() {
        return this.isopen;
    },

    postDraw: function() {
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
             return IndicoUtil.markInvalidField(element, text);
         },

         setError: function(text) {
             if (!text) {
                 // everything back to normal
                 if (this._stopErrorList){

                     each(this._stopErrorList,
                          function(elem) {
                              elem();
                          });

                     this._stopErrorList = [];
                 }
             } else {
                 this._setErrorState(text);
             }
             return this._stopErrorList;
         }},
     function() {
     });
