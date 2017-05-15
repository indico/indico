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

var TimetableDefaults = {
    topMargin: 30,
    bottomMargin: 40,
    leftMargin: 55,
    rightMargin: 5,
    resolution: 1,
    menuWidth: 150,
    blockMargin: 4,        // Margin used inside timetable blocks
    wholeday : 7,              // # of hours of duration for a timetable event to be seen as be during the whole day.
    minContribHeight: 20,      // Minimum height for a contrib displayed inside a session TODO: remove?
    layouts: {'compact': {name: "Compact",
                          values : {
                              pxPerHour: 150,
                              pxPerSpace: 2,
                              minPxPerBlock: 50
                          },
                          manager: new CompactLayoutManager()},

              'proportional': {name: 'Proportional',
                               values : {
                                   pxPerHour: 120, //50 when not proportional
                                   minPxPerBlock: 25
                               },
                               manager: new ProportionalLayoutManager()
                              },

              'poster': {name: 'Poster',
                         manager: new PosterLayoutManager()
                        },

              'room': {name: 'Room',
                       manager: new RoomLayoutManager()
                      }
             },
    filters: {'session': {name: $T('Session'),
                          filter: new SessionFilter()},
              'room': {name: $T('Room'),
                       filter: new RoomFilter()}}
};


type("TimeTable", ["HistoryListener"], {

    /*
     * Translates the keys used in the data dictionary into titles
     * displayed in the tab control
     */


    _draw: function(timetableDiv) {
        return $('<div/>').css({width: this.width}).append(
            $('<div/>').css('display', 'block'),
            this.legend,
            this.header,
            timetableDiv.dom,
            this.loadingIndicator.dom).get();
    },

    _getMenu: function() {
        return Html.div();
    },

    postDraw: function() {
        this.timetableDrawer.postDraw();
        //this.LookupTabWidget.prototype.postDraw.call(this);
    },

    getData: function() {
        return this.data;
    },

    get_elem: function(blkId) {
        return $(this.getTimetableDrawer()._blockMap[blkId]);
    },

    getById: function(id) {

        var info = Util.parseId(id);
        var type = info[0];
        var compositeId = "";
        info = info.slice(2);

        if (type == 'Conference') {
            return this.eventInfo;
        }
        else if (type == 'Contribution') {
            throw 'not implemented!';
        } else if (type=='Session'){
            return this.eventInfo.sessions[info[0]];
        } else if (type=='SessionSlot'){
            compositeId = 's'+info[0]+'l'+info[1];
        } else {
            throw 'unrecognized id!';
        }

        for (var day in this.data) {
            if (this.data[day][compositeId]) {
                return this.data[day][compositeId];
            }
        }
    },

    setSelectedTab: function(val) {
        // same as inherited, but return deferred
        var dfr = $.Deferred();
        $('body').one('timetable_ready', function() {
            dfr.resolve();
        });
        this.JLookupTabWidget.prototype.setSelectedTab.call(this, val);
        return dfr.promise();
    },

    getTimetableDrawer: function() {
        return this.timetableDrawer;
    },

    setData: function(data, intervalData, startTime, endTime) {
            this.timetableDrawer.setData(data, startTime, endTime);
    },

    _createLoadingIndicator: function() {
        return Html.div('timetableLoading', $T('Updating the timetable...'));
    },
    /*
      * To be overloaded. Header content displayed above the timetable.
      */
    _getHeader: function() {
        return Html.div({});
    },

    /*
      * To be overloaded. Returns the small "Session legend" displayed in
      * detailed mode (only).
      */
    _getLegend: function() {
            return Html.div({});
    },
    /*
      * To be overloaded. Returns buttons to be displayed below the tabs in
      * the tab widget.
      */
    _functionButtons: function() {
        return [];
    },

    //To be overloaded
    redrawLegend: function() {
        return;
    }

},
     function(data, width, wrappingElement, detailLevel, managementMode) {
         var self = this;
         this.data = data;

         this.enabled = true;

         this.processedWarnings = new WatchList();

         this.width = width;
         this.loadingIndicator = this._createLoadingIndicator();
         this.header = this._getHeader();
         this.legend = $('<div/>');
     }
    );


type("DisplayTimeTable", ["TimeTable"], {

    filterMenu: function() {
        var self = this;

        var filterLink = Html.a({href: '#'}, $T("Filter"));
        this.filterMenu = new TimetableFilterMenu(filterLink, self.timetableDrawer);

        filterLink.observeClick(function(e) {
            var pos = filterLink.getAbsolutePosition();
            self.filterMenu.open(pos.x + filterLink.dom.offsetWidth, pos.y);
            return false;
        });

        return Html.ul({className: "inner", style: {display: 'none'}},
                       Html.li("menuConfMiddleCell",
                               filterLink));
    },

    printMenu: function() {
        var self = this;

        var printLink = Html.a({href: '#'}, $T("Printable version"));
        printLink.observeClick(function(e) {

            self.print();

        });
        return Html.ul({className: "inner", style: {display: 'none'}},
                       Html.li("menuConfMiddleCell",
                               printLink));
    },
    print: function() {
        var self = this;

        self.timetableDrawer.setPrintableVersion(true);
        var timetableElements = translate(self.timetableDrawer.canvas.dom.childNodes, function(value) {return value;});

        var goBackLink = $('<a/>').prop('href', window.location.hash).html($T('Go back')).css('font-size', '17px');
        var separator = $('<a/>').html(' | ').css('fontSize', '17px');
        var printLink = $('<a/>').prop('href', window.location.hash).html($T('Print')).css('font-size', '17px');

        var links = $('<span/>').append(goBackLink, separator, printLink).css('float', 'right');

        var header = $('<div/>').addClass('timetableHeader clearfix').append(links).css({'padding': '0px 5px 5px 5px',
                                                                                        'border-bottom': '1px solid black',
                                                                                        'text-align': 'center',
                                                                                        'width': self.timetableDrawer.width});
        header.append($('<span/>').append(self._titleTemplate(self.timetableDrawer.day)).css('float', 'left'));

        goBackLink.click(function() {
            location.reload();
        });

        printLink.click(function() {
            window.print();
        });

        var timetableDiv = $('<div/>').append(timetableElements).css({'padding-top': '20px', 'position': 'relative'});

        $("body").html(header.add(timetableDiv));
        $("body").css("padding", "30px");
    },

    pdf: function() {
        if ($('html').data('static-site')) {
            window.location = build_url(Indico.Urls.Timetable.default_pdf, {confId: this.eventInfo.id});
        } else {
            ajaxDialog({
                url: build_url(Indico.Urls.Timetable.pdf, {confId: this.eventInfo.id}),
                title: $T.gettext('Export to PDF')
            });
        }
    },

    fullScreen: function() {
        var self = this;

        IndicoUI.Dialogs.Util.progress($T("Switching to full screen mode..."));
        // This timeout is needed in order to give time to the progress indicator to be rendered
        setTimeout(function(){
            self.timetableDrawer.width = $(window).width() - 50; // 50 is a width offset.

            var header = $('<div/>').addClass('timetableFullScreenHeader clearfix').css('width', self.timetableDrawer.width);
            header.append($('<span/>').append(self._titleTemplate(self.timetableDrawer.day)).css('float', 'left'));

            var timetableCanvas = $('#timetable_canvas');
            $('#timetable_canvas').width('width', self.timetableDrawer.width);
            $("body").html(header);
            $("body").css("padding", "30px");
            $(".timetableFullScreenHeader").before(self._getExtraButtons());
            $(".timetableFullScreenHeader").before(self.legend);
            $(".timetableFullScreenHeader").after(timetableCanvas);
            self.timetableDrawer.redraw(self.currentDay);

            self._filterSetup();
            if (self.timetableDrawer.detail.get() == 'contribution') {
                var newDetailLevel = self.timetableDrawer.detail.get() == 'contribution' ? 'session' : 'contribution';
                self.timetableDrawer.detail.set(newDetailLevel);
                self.toggleDetailedView();
            }
        }, 50);
    },

    _getExtraButtons: function() {
        var self = this;
        var container = $('<div class="tabExtraButtons"/>');
        var goBackButton = {'btn': Html.div('buttonWhite', $T('Exit Full Screen')),
            'onclick': function(btnContainer) {
                location.reload();
            }
        };
        var buttons = self._functionButtons();
        buttons[2] = goBackButton;
        $.each(buttons, function(i, btnData) {
            var btn = $('<div class="buttonContainer"/>').append(btnData.btn.dom || btnData.btn).click(function() {
                btnData.onclick(btn);
            });
            container.append(btn);
        });
        container.children(':first').addClass('buttonContainerLeft');
        container.children(':last').addClass('buttonContainerRight');
        goBackButton.btn.getParent().dom.style.background ="#9F883B";
        return container;
    },

    _filterSetup: function() {
        var self = this;
        this.filter = new TimeTableFilter(this.timetableDrawer, function () {
            // When closed restore the filter button color
            self.filterButtonContainer.css('background', '');
            return true;
        });
        this.filter.draw();
    },

    toggleDetailedView: function() {
        var self = this;
        var detailLevel = this.timetableDrawer.detail.get();
        var newDetailLevel = detailLevel == 'contribution' ? 'session' : 'contribution';
        this.timetableDrawer.detail.set(newDetailLevel);
        var state = (newDetailLevel == 'contribution');
        this.inDetailedMode = state;
        //detailsButton.btn.set(state ? "Hide details" : "Show details");
        this.detailsButton.btn.getParent().dom.style.background = state ? "#9F883B" : "";
        this._addToHistory(this.currentDay + (state?'.detailed':''));

        var legend;

        //If the "Detailed view" button is clicked and "activated".
        if(this.inDetailedMode) {
            /* Draw legend or "undraw" legend (getLegend() returns an empty div)
               when toggling for detailed view. */
            legend = this._getLegend();
            this.legend.replaceWith(legend);

            if (this._legendActive) {
                self._toggleLegend(true);
            } else {
                self._legendPostDraw();
            }
        } else {
            if (this._legendActive) {
                self._toggleLegend(false);
            }
            legend = $('<div/>');
            this.legend.replaceWith(legend)

        }
        this.legend = legend;
    },

    _functionButtons: function() {
        var self = this;

        this.printButton = {'btn': Html.div('printButtonWhite', $T('Print')),
            'onclick': function(btnContainer) {
                self.print();
            }
        };

        this.pdfButton = {'btn': Html.div('buttonWhite', $T('PDF')),
            'onclick': function(btnContainer) {
                self.pdf();
            }
        };

        this.fullScreenButton = {'btn': Html.div('buttonWhite', $T('Full screen')),
            'onclick': function(btnContainer) {
                self.fullScreen();
            }
        };

        // TODO: Needs to be implemented
        this.linkButton = Html.div('linkButtonWhite', $T('Link'));

        this.detailsButton = {'btn': Html.div({className: 'buttonWhite', id: 'detailsButton'},
                                               Html.span({}, $T('Detailed view'))),
            'onclick': function() {self.toggleDetailedView();}};

        this.filterButton = {'btn': Html.div('buttonWhite', $T('Filter')),
            'onclick': function(btnContainer) {
              // Save the container so that the filter button background
              // color can be restored when filter is closed
              self.filterButtonContainer = btnContainer;
              self.filter.toggle();
              var state = self.filter.state.get();
              self._filterActive = state;
              btnContainer.css('background', state ? "#9F883B" : "");
            }
        };

        return [this.printButton,
                this.pdfButton,
                this.fullScreenButton,
                this.detailsButton,
                this.filterButton];
        }
    },
     function(data, width, wrappingElement, detailLevel) {
         this.TimeTable(data, width, wrappingElement, detailLevel, false);

         // Set data[all] so that the All days tab is created
         if (keys(data).length > 1) {
             this.data.all = data;
         }
     }
    );


type("TopLevelTimeTableMixin", ["JLookupTabWidget"], {

    draw: function() {
      return this.JLookupTabWidget.prototype.draw.call(this);
    },

    getDays: function() {
        return this.sortedKeys;
    },

    disable: function() {
        this.enabled = false;
        this.JLookupTabWidget.prototype.disable.call(this);
    },

    enable: function() {
        this.enabled = true;
        this.JLookupTabWidget.prototype.enable.call(this);
    },

    _titleTemplate : function(text) {
        if (text == 'all') {
            return $T('All days');
        }

        var day = text.substring(6,8);
        var month = text.substring(4,6);

        var strDate =  day + '/' + month + '/' + text.substring(0,4);

        //var nDate = new Date();
        var delements = parseDate(strDate);
        var nDate = new Date(delements[2], delements[1]-1, delements[0]);

        return Indico.Data.WeekDays[nDate.getDay()].substring(0,3)+' '+day+'/'+month;

    },


    _parseDayInterval: function(hash) {
        var m = hash.match(/#(\d{8}|all)(?:\.((?:s\d+)|detailed))?/);

        if (m) {
            return [m[1],m[2]];
        } else {
            return [null, null];
        }
    },

    switchToInterval : function(intervalId) {
        var dfr = $.Deferred();
        this.disable();

        var intervalInfo = this.data[this.currentDay][intervalId];
        var data = intervalInfo.entries;

        this.intervalTimeTable = new IntervalManagementTimeTable(this,
                                                                 data,
                                                                 intervalInfo,
                                                                 this.eventInfo,
                                                                 this.width.slice(0,-2),
                                                                 this.canvas[0],
                                                                 'contribution',
                                                                 this.isSessionTimetable,
                                                                 this.customLinks,
                                                                 this.canManageSession,
                                                                 this.canManageBlocks,
                                                                 this.canManageContribs);

        this.intervalTimeTable.setData(intervalInfo);
        var content = this.intervalTimeTable.draw();
        this.canvas.html(content[0]);
        this.intervalTimeTable.postDraw();

        $('body').trigger('timetable_switch_interval', this.intervalTimeTable);

        dfr.resolve();
        return dfr.promise();
    },

    postDraw: function() {
        this.TimeTable.prototype.postDraw.call(this);
    },

    switchToTopLevel : function(day) {
        day = day || this.currentDay;
        var dfr = $.Deferred();
        this.enable();
        this.setSelectedTab(day || this.currentDay);
        this._generateContent(this.getSelectedPanel());
        this.timetableDrawer.redraw();

        // Refresh header (menu, etc...)
        var header = this._getHeader();
        this.header.replaceWith(header);
        this.header = header;

        $('body').trigger('timetable_switch_toplevel', this);
        window.location = '#' + day;

        dfr.resolve();
        return dfr.promise();
    }
},
     function(data, width, wrappingElement, detailLevel, managementActions, historyBroker, timetableLayoutId) {

         var self = this;

         this.managementActions = managementActions;

         this.canvas = Html.div({});

         historyBroker.addListener(this);

         this.timetableDrawer = new TimetableDrawer(this, width,
                                                    wrappingElement,
                                                    detailLevel,
                                                    this._functionButtons(),
                                                    this.loadingIndicator,
                                                    !!managementActions,
                                                    managementActions,
                                                    timetableLayoutId);

         this.sortedKeys = keys(this.data);
         this.sortedKeys.sort();


         var today = new Date();
         var todayStr = IndicoUtil.formatDate2(today);

         var originalHash = window.location.hash;

         var dayAndInterval = this._parseDayInterval(originalHash);
         var initialTab = null;

         if (dayAndInterval[0]) {
             initialTab = dayAndInterval[0];
         }

         // if nothing is found
         if (initialTab === null) {
             // look for today
             if (exists(data[todayStr])) {
                 initialTab = todayStr;
             } else {
                 // look for the first non-empty day
                 for (var day in this.data) {
                     if (Object.getOwnPropertyNames(this.data[day]).length > 0) {
                         initialTab = day;
                         break;
                     }
                 }
                 if (initialTab === null) {
                     // otherwise show the first day
                     initialTab = this.sortedKeys[0];
                 }
             }
         }

         this.currentDay = initialTab;

         this.JLookupTabWidget(translate(this.sortedKeys, function(key) {

             return [key, function() {

                 var detailed = self.inDetailedMode?'.detailed':'';

                 self.currentDay = key;
                 // each time one tab is clicked,
                 // drawDay is called over a different day
                 if (key == 'all') {
                     self._addToHistory('all' + detailed);
                     return self._draw(self.timetableDrawer.drawAllDays());
                 } else {

                     // Are we switching to interval mode
                     if (!self.enabled) {
                         // stop everything, we don'w want the LookupTabWidget
                         // to replace the contents
                         throw "stopDrawing";
                     }

                     self._addToHistory(key + detailed);
                     return self._draw(self.timetableDrawer.drawDay(key));
                 }
             }];
         }), this.width, 100, initialTab, this._functionButtons(), this.canvas);
         this.makeScrollable();

         if (dayAndInterval[1]) {
             var subref = dayAndInterval[1];
             // TODO: replace with appropriate notification system
             setTimeout(function() {
                 if (subref == 'detailed') {
                     self.toggleDetailedView();
                 } else {
                     self.switchToInterval(subref);
                 }
             }, 500);
         }

     });


type("IntervalTimeTableMixin", [], {

    draw: function() {
        // Add hash to history
        this.parentTimetable._addToHistory(this.currentDay + '.' + this.contextInfo.id);

        return this._draw(this.timetableDrawer.drawDay(this.currentDay));
    },

    _getInfoBoxContent: function() {

        return Html.div({}, Html.span({style: {fontStyle: 'italic', fontSize: '0.9em'}},
            $T('You are viewing the contents of the session block:')),
            Html.div({style: {fontWeight: 'bold', marginTop: '5px', fontSize: '1.3em'}},
            this._generateSlotTitle(this.contextInfo),
            Html.span({style: {fontWeight: 'normal'}},
            " (", $B(Html.span({}), this.slotStartTime), " - ", $B(Html.span({}), this.slotEndTime),")" )));
    },

    postDraw: function() {
        this.timetableDrawer.postDraw();
    },

    setData: function(data) {
        var day = IndicoUtil.formatDate2(IndicoUtil.parseJsonDate(data.startDate));
        var ttData = {};

        this.data = data.entries;

        // WatchValues, so that interval changes can be handled
        this.slotStartTime = new WatchValue(data.startDate.time.substring(0,5));
        this.slotEndTime = new WatchValue(data.endDate.time.substring(0,5));

        ttData[day] = data.entries;

        this.currentDay = day;
        this.timetableDrawer.setData(ttData, day, data.isPoster);

        // The time must be update each time new data is set
        this.infoBox.set(this._getInfoBoxContent());

    },

    getDays: function() {
        return this.parentTimetable.getDays();
    },

    getById: function(id) {
        return this.parentTimetable.getById(id);
    }


},
     function(parent, width, wrappingElement, managementActions, layout) {

         this.managementActions = managementActions;
         this.parentTimetable = parent;

         this.timetableDrawer = new IntervalTimetableDrawer(this, width,
                                                            wrappingElement,
                                                            this._functionButtons(),
                                                            this.loadingIndicator,
                                                            !!managementActions,
                                                            managementActions,
                                                            layout || 'compact');
     });


type("ManagementTimeTable",["TimeTable", "UndoMixin"], {

    _generateSlotTitle: function(slotData) {
        return slotData.title + (slotData.slotTitle ? ": " + slotData.slotTitle : '');
    },


    _createInfoArea: function() {

        // this is a client-side hack that compensates some algorithm weaknesses

        var closeButton = Html.div({
            className: 'balloonPopupCloseButton',
            style: {position: 'absolute',
            top: '10px',
            right: '10px',
            padding: '0px'}
        });

        var self = this;

        closeButton.observeClick(function() {
            self._hideWarnings();
        });

        return Html.div("timetableManagementInfoArea",
                        Html.div({}, $T("Your changes triggered the automatic modification of some settings:")),
                        $B(Html.ul({}),
                           this.processedWarnings,
                           function(item) {

                               var title = item[4];
                               var atoms = Util.parseId(item[1]);

                               var message = {
                                   OWNER_START_DATE_EXTENDED: {
                                       SessionSlot : $T('The <strong>starting time</strong> of the session interval <strong>')  + title + $T('</strong> was moved from '),
                                       Session: $T('The <strong>starting time</strong> of the session interval <strong>')  + title  + $T('</strong> was moved from '),
                                       Conference: $T('The <strong>starting time</strong> of the <strong>Event</strong> was moved from ')
                                   },
                                   OWNER_END_DATE_EXTENDED: {
                                       SessionSlot : $T('The <strong>ending time</strong> of the session interval <strong>') + title + $T('</strong> was moved from '),
                                       Session: $T('The <strong>ending time</strong> of the session interval <strong>') + title + $T('</strong> was moved from '),
                                       Conference: $T('The <strong>ending time</strong> of the <strong>Event</strong> was moved from ')
                                   },
                                   ENTRIES_MOVED: {
                                       SessionSlot: $T('The contents of the interval <strong>') + title + $T('</strong> were moved from ')
                                   }
                               }[item[0]][atoms[0]];

                               var span = Html.span({style: {verticalAlign: 'middle', marginLeft: '5px'}});
                               span.dom.innerHTML = message + ' <strong>' + item[3] +
                                   '</strong>' + $T(' to ') + '<strong>' + item[2] + '</strong>' ;
                               return Html.li({}, span);
                           }),
                       closeButton);
    },


    _updateMovedEntry: function(result, oldEntryId) {
        return this._updateEntry(result, oldEntryId, function(data) {
            var oldDate = IndicoUtil.formatDateTime(IndicoUtil.parseJsonDate(result.old.startDate), 'd/MM/YYYY hh:mm');
            var oldDay = Util.formatDateTime(Util.parseDateTime(oldDate, IndicoDateTimeFormats.Default),
                                             IndicoDateTimeFormats.Ordinal);
            if (result.old.sessionId) {
                // block was inside session slot
                delete data[oldDay]['s' + result.old.sessionSlotEntryId].entries[result.old.id];
            } else {
                // block was in top level
                delete data[oldDay][result.old.id];
            }

            if (result.slotEntry) {
                // block moves inside session slot
                data[result.day][result.slotEntry.id].entries[result.id] = result.entry;
                // updates the time of the session if it has to be extended
                data[result.day][result.slotEntry.id].startDate.time = result.slotEntry.startDate.time;
                data[result.day][result.slotEntry.id].endDate.time = result.slotEntry.endDate.time;
                data[result.day][result.slotEntry.id].duration = result.slotEntry.duration;
            } else {
                // block moves to top level
                data[result.day][result.id] = result.entry;
            }
        });
    },

    /*
     *
     * Is called every time a timetable entry has been successfully
     * added or updated. Updates and redraws the timetable.
     * @param originalArgs this are the original args. If they are passed, we can remove the entry
     * from the index before adding it again (just in case the date has changed).
     *
     */

    _processAutoOps: function(result) {
        this._hideWarnings();

        var self = this;

        if (result.autoOps && result.autoOps.length > 0) {
            each(result.autoOps,
                 function(op) {

                     var warning = self._processWarning(op);
                     if (warning && self.processedWarnings.indexOf(warning) === null) {
                         self.warningArea.dom.style.display = 'block';
                         self.processedWarnings.append(warning);
                     }
                 });
        }
    },

    _hideWarnings: function() {
        this.warningArea.dom.style.display = 'none';
        this.warnings.clear();
        this.processedWarnings.clear();
    },

    _processWarning: function(entry) {
        /*
         * entry - the warning 'entry', a list [src, msg, target, newValue]
         * startTime - the original starting time for the timeblock
         * endTime - the original ending time for the timeblock
         * [slotTitle] - title, if the entry is a slot
         */

        var msg = entry[1];
        var finalTime = entry[3];

        var type = Util.parseId(entry[2])[0];

        var conference = null;
        var slot = null;
        var title = "";

        var startTime = "";
        var endTime = "";

        if (type == "Session") {
            return null;
        } else if (type == 'Conference') {
            conference = this.getById(entry[2]);
            title = conference.title;
            startTime = conference.startDate.time.slice(0,5);
            endTime = conference.endDate.time.slice(0,5);
        } else if (type == 'SessionSlot') {
            slot = this.getById(entry[2]);
            startTime = slot.startDate.time.slice(0,5);
            endTime = slot.endDate.time.slice(0,5);
            title = this._generateSlotTitle(slot);
        }

        if (msg == "OWNER_END_DATE_EXTENDED") {
            // Make sure that something changed, otherwise the
            // warning will be supressed
            if (endTime != finalTime) {
                // slice(1) to ignore first value
                return concat(entry.slice(1),  [endTime, title]);
            }
        } else if (msg == "OWNER_START_DATE_EXTENDED") {
            // Again, make sure that something changed

            if (startTime != finalTime) {
                // slice(1) to ignore first value
                return concat(entry.slice(1), [startTime, title]);
            }
        } else {
            return concat(entry.slice(1), [startTime, title]);
        }

        return null;
    },

    _allowCreateHere: function(elementType) {
        switch(elementType) {
        case 'Session':
            return (this.contextInfo._type == "Conference");
        case 'Break':
            return (this.contextInfo._type == "Conference" ? true : (this.contextInfo.isPoster === false));
        case 'Contribution':
            return true;
        }

    },

    _retrieveSessionColor: function(session){
        return this.getById("s"+session.id).color;
    },

    _openSessionMenu: function(triggerElement, parent) {

        if (exists(this.addMenu) && this.addMenu.isOpen()) {
            return;
        }

        var self = this;

        var menuItems = {};

        var sessions = {};
        each(this.eventInfo.sessions, function(session, key) {
            sessions[session.id] = {};
            sessions[session.id].func = function() { self.managementActions.addSessionSlot(session); };
            sessions[session.id].color = self._retrieveSessionColor(session);
            sessions[session.id].title = session.title;
        });

        var menu = {
            '' : {content: {'Create a new session': function() {
                self.managementActions.addSession();
                $('.button-menu').dropdown('close');
            }}, description: ''},
            'Add another block to:': {content: sessions, description: ''}
        };

        var te = new Html(triggerElement.find('a').get(0));
        var sessMenu = new SessionSectionPopupMenu(menu, [te], 'timetableSectionPopupList popupListChained', true, true);

        var pos = triggerElement.offset();
        sessMenu.open(pos.left, pos.top - 1);
    },

    _createAddMenu: function(elem) {
        var self = this;
        var menuItems = {};
        var ul = $('<ul class="dropdown"/>');

        if (this._allowCreateHere('Session')) {
            var sessionAdd = $('<a href="#"/>').text($T('Session block')).appendTo(ul).wrap("<li/>");
            sessionAdd.bind('menu_select', function() {
                if (keys(self.eventInfo.sessions).length === 0) {
                    $(this).closest('.group').dropdown('close');
                    self.managementActions.addSession();
                } else {
                    self._openSessionMenu($(this).parent(), ul);
                }
                return true;
            });

        }

        if (this._allowCreateHere('Contribution')){
            $('<a href="#"/>').text($T('Contribution')).bind('menu_select', function() {
                self.managementActions.addContribution();
                // Dirty hack to avoid Chrome glitch
                $(this).closest('.group').dropdown('close');
                return false;
            }).appendTo(ul).wrap("<li/>");
        }
        if (this._allowCreateHere('Break')){
            $('<a href="#"/>').text($T('Break')).bind('menu_select', function() {
                self.managementActions.addBreak();
                $(this).closest('.group').dropdown('close');
                return false;
            }).appendTo(ul).wrap("<li/>");
        }

        return ul;

    },

    _getHeader: function() {

        var self = this;

        this.infoBox = Html.div({className: 'timetableInfoBox'});

        this.addMenuLink = this.contextInfo.isPoster ?
            $('<a href="#" data-toggle="menu_select"/>').text($T('Add poster')).bind('menu_select', function() {
                self.managementActions.addContribution();
            }) : $('<a href="#" id="add_new" class="arrow hide-if-locked" data-toggle="dropdown">').text($T('Add new'));


        this.rescheduleLink = $('<a href="#" class="hide-if-locked" data-toggle="menu_select">').text($T('Reschedule'));
        this.rescheduleLink.bind('menu_select', function() {
            var popup = new RescheduleDialog(self);
            popup.open();
            return false;
        });

        this.fitInnerTimetableLink = $('<a href="#" class="hide-if-locked" data-toggle="menu_select">').text($T('Fit to content'));
        this.fitInnerTimetableLink.bind('menu_select', function() {
            var popup = new FitInnerTimetableDialog(self);
            popup.open();
            return false;
        });

        this.addIntervalLink = $('<a href="#" class="hide-if-locked" data-toggle="menu_select"/>').text($T('Add new block'))
        this.addIntervalLink.bind('menu_select', function() {
            self.managementActions.addSessionSlot(self.eventInfo.timetableSession);
            return false;
        });


        var customLinks = $();
        for(var linkName in this.customLinks){
            var link = $('<a href="#" class="hide-if-locked">').text(linkName)
                                         .addClass('js-{0}'.format(this.customLinks[linkName]))
                                         .data('timetable', self);
            customLinks = customLinks.add(link);
        }

        this.warningArea = this._createInfoArea();
        this.warningArea.dom.style.display = 'none';

        this.menu = $('<div class="group"/>');

        if (this.isSessionTimetable && this.isTopLevel) {
            if (this.canManageBlocks) {
                this.menu.append(this.addIntervalLink);
            }
        }
        else {
            this.menu.append(this.addMenuLink);
        }

        if (!this.contextInfo.isPoster) {
            if (this.canManageBlocks) {
                if (this.contextInfo.entryType == 'Session') {
                    this.fitInnerTimetableLink.appendTo(this.menu);
                }
                this.rescheduleLink.appendTo(this.menu);
            }
        }

        customLinks.appendTo(this.menu);

        var tt_hour_tip = $('<div id="tt_hour_tip"/>').hide().append($('<img/>').prop('src', imageSrc('tt_time')).prop('title', $T("Add one hour")));
        var tt_status_info = $('<div id="tt_status_info" />');

        this.menu.children('a').addClass('i-button');

        if (!this.contextInfo.isPoster && (!this.isTopLevel || !this.sessionTimetable)) {
            this.menu.find('#add_new').after(this._createAddMenu(this.addMenuLink.parent()));
        }

        var ret = $('<div/>').append(
            this.warningArea.dom,
            $('<div id="headPanel" class="ui-follow-scroll"></div>').append($('<div class="toolbar f-j-end" id="tt_menu"/>').
                append(this.menu.dropdown({effect_on: 'slideDown'}),
                        tt_status_info, this.infoBox.dom)),
            tt_hour_tip);

        var extra = this.getTTMenu();
        if (extra) {
            ret.find('#tt_menu .group').after(extra);
        }

        return ret;
    }

},
     function(data, contextInfo, eventInfo, width, wrappingElement, detailLevel, customLinks,
              canManageSession, canManageBlocks, canManageContribs, canManageEvent) {
         this.customLinks = customLinks;
         this.eventInfo = eventInfo;
         this.contextInfo = contextInfo;
         this.canManageSession = canManageSession || false;
         this.canManageBlocks = canManageBlocks || false;
         this.canManageContribs = canManageContribs || false;
         this.canManageEvent = canManageEvent || false;
         this.warnings = new WatchList();
         this.TimeTable(data, width, wrappingElement, detailLevel, true);
     }
    );


type("TopLevelDisplayTimeTable", ["DisplayTimeTable", "TopLevelTimeTableMixin"], {

    _retrieveHistoryState: function(hash) {
        var currentDay = this._parseDayInterval(hash)[0];
        this.setSelectedTab(currentDay);
    },

    _getLegend: function() {
        var self = this;
        //Initially show N and have the rest hidden (buried under "...more")
        self._maxLegendItemsShownInitially = 4;

        var toggleLegendButton = $('<div id="legendMainToggle">' +
                                   $T("Session legend") + '</div>');

        if (this._legendActive) {
            toggleLegendButton.addClass('active');
        }

        toggleLegendButton.click(function() {
            self._legendActive = !self._legendActive;
            self._toggleLegend(self._legendActive);
        });

        self._toggleLegendButton = toggleLegendButton;

        this.legendItems = self._legendItemsContainer();
        // hide it so that we can execute the nice scroll down animation
        this.legendItems.hide();

        // create 'update' event that will be called when the day changes (redraw)
        this.legendItems.bind('update', function(){
            $(this).html(self._legendItemsContainer().children());
            if (self._legendActive && self.legendSessionInfo[self.currentDay].length){
                $(this).slideDown();
            } else {
                $(this).slideUp();
            }
            self._legendPostDraw();
        });

        return $('<div id="wholeLegend"/>').append(toggleLegendButton).append(this.legendItems);
    },

    _legendItemsContainer: function() {
        var self = this;
        var state = false;
        var moreText = $T("see more...");
        var showMoreLink = $('<a id="showMoreLink" class="showMoreLink">' + moreText + '</a>').click(
            function() {
                if(!state) {
                    self._fadeShowAllLegendItems();
                    showMoreLink.text($T('less...'));
                } else{
                    self._fadeHideLegendItems();
                    showMoreLink.text(moreText);
                }
                self._legendPostDraw();
                state = !state;
            });

        var closeButton = $('<div class="legendCloseButton"/>').click(function() {
            self._toggleLegend(false);
            self._legendActive = false;
        });

        var sessions = self.legendSessionInfo[this.currentDay];
        var container = $('<div id="timeTableLegend" class="timeTableLegend ui-follow-scroll">').append(closeButton);

        if (sessions.length) {
            // Returns a div with each color + session name element
            var legendElements = self._generateLegendDivItems(sessions);
            container.append($('<div id="legendItemContainer"/>').append(legendElements));
            if (sessions.length > self._maxLegendItemsShownInitially) {
                container.append(showMoreLink);
            }
        }
        return container;
    },

    // Generates the "legend items"
    // (a small colored rounded square with the sessions title on its right hand side)
    // Returns a Div with those legend element items.
    _generateLegendDivItems: function(sessions) {
        var self = this;
        var showNumSessionsCounter = 0;
        var container = $('<div>');

        $.each(sessions, function(idx, l){
            var div =  $('<div class="legendItem" />').
                append($('<div class="timeTableItemColour" />').css('background', l[2]),
                       $('<span/>').text(l[1]));

            container.append(div);

            if (idx >= self._maxLegendItemsShownInitially){
                div.hide();
            }
        });
        return container;
    },

    redrawLegend: function() {
        if (this.legendItems) {
            this.legendItems.trigger('update');
        }
    },

    // Used by the "...more"-button when you want to show more elements
    _fadeShowAllLegendItems: function() {
        $('.legendItem').fadeIn();
    },

    // Used by the "...less"-button when you want to hide more elementsmaxLegendItemsShownInitially
    // Note, it does NOT HIDE ALL: depending on "maxLegendItemsShownInitially".
    _fadeHideLegendItems: function() {
        $('.legendItem').slice(this._maxLegendItemsShownInitially).fadeOut();
    },

    /* This function is also called in "this.filterButton" in order
       to hide it (the Session Legend) when the Filter is brought up */
    _toggleLegend: function(state) {
        var self = this;

        if (state) {
            $('#legendMainToggle').addClass('active');
            if (this.legendSessionInfo[this.currentDay].length) {
                $('#timeTableLegend').slideDown();
            }
        } else {
            $('#timeTableLegend').slideUp();
            $('#legendMainToggle').removeClass('active');
        }
        this._legendPostDraw();
    },

    _legendPostDraw: function() {
        var self = this;
        // loop for truncation of too long session titles,
        // the text next a coloured box in the "session legend".
        var initialTruncing = null;
        var i = 0;

        // Loop through each legend item
        $('.legendItem').each(function(){
            var titleIsTruncated = false;
            var fullTitle = $(this).text();
            initialTruncing = fullTitle.length;
            // Keep truncating the title until its short enough to be written in
            // one line and still less wide than the
            // "maximum legend item width".

            var span = $(this).children('span');

            while(span.get(0).offsetHeight > 25 || span.get(0).offsetWidth > 130) {
                titleIsTruncated = true;
                var truncSessionTitle = TimetableBlockBase.prototype.truncateTitle(--initialTruncing, fullTitle);
                span.html(truncSessionTitle);
            }

            if(titleIsTruncated) {
                $(this).qtip({content: fullTitle, position: {my: 'top middle', at: 'bottom middle'}});
            }
        });

        if ($('#detailsButton').length) {
            $('#legendMainToggle').position({my: 'left top',
                                             at: 'left bottom',
                                             of: $('#detailsButton').parent('.buttonContainer')});
            $('#timeTableLegend:visible').width($('#timeTableLegend').get(0).clientWidth-10);
        }

    },

    _extractSessionInfo: function(data) {
        // get an a dictionary where the keys are days and the values are lists
        // of [id, title, color] tuples (sessions only)
        var days = {};

        _(data).each(function(entries, day) {
            days[day] = _(entries).chain().
                select(function(e) { return e.entryType == 'Session'; }).
                groupBy(function(e) { return e.sessionId; }).
                reduce(function(l, s) { return l.concat(s[0]); }, []).
                map(function(e){ return [e.id, e.title, e.color, e.sessionId]; }).
                sortBy(function(e){ return e[1]; }).
                value();
        });

        // for "all days", put it all together
        days['all'] = _(days).chain().
            flatten(true).
            groupBy(function(e) { return e[3]; }).
            reduce(function(l, s) { return l.concat([s[0]]); }, []).
            sortBy(function(e){ return e[1]; }).
            value();

        return days;
    }
},
     function(data, contextInfo, width, wrappingElement, detailLevel, historyBroker, timetableLayoutId) {
         this.postDraw = TopLevelTimeTableMixin.prototype.postDraw;
         this.legendSessionInfo = this._extractSessionInfo(data);
         this._legendActive = true;

         this.DisplayTimeTable(data, width, wrappingElement, detailLevel);
         this.TopLevelTimeTableMixin(data, width, wrappingElement, detailLevel, null, historyBroker, timetableLayoutId);

         this.eventInfo = contextInfo;
         this._filterSetup();
     });


type("TopLevelManagementTimeTable", ["ManagementTimeTable", "TopLevelTimeTableMixin"], {

    _deleteOldEntry: function(data, result, oldEntryId) {
        /*
         * Deletes the old version of the entry
         */

        var oldStartDate;
        // Check whether we're operating *over* an existing slot or not
        // it is a slot && slot exists in timetable
        if (result.entry.entryType == "Session" && data[this.currentDay][result.id]) {
            var slot = data[this.currentDay][result.id];
            oldStartDate = slot.startDate.date.replace(/-/g, '');
        } else {
            // Contribution or break - event timetable limits
            oldStartDate = this.currentDay;
        }

        delete data[oldStartDate][oldEntryId];
        return data[oldStartDate][oldEntryId] ? data[oldStartDate][oldEntryId].entries : null;

    },

    _updateEntry: function(result, oldEntryId, updateCycle) {
        var self = this;
        var data = this.getData();

        // AutoOp Warnings (before updates are done)
        this._processAutoOps(result);

        // Deletes the old version of the entry and temporarily
        // stores the entry contents to be used later on this function
        var oldContent = this._deleteOldEntry(data, result, oldEntryId);

        // Here's the update cycle
        if (updateCycle) {
            updateCycle(data);
        } else {
            // If none is defined in the function args,
            // execute the default action
            if (exists(result.slotEntry)){
                data[result.day][result.slotEntry.id].entries[result.entry.id] = result.entry;
            } else {
                data[result.day][result.id] = result.entry;
            }

            // A session interval may contain entries, that
            // should be preserved (e.g. content (contribs, breaks) of
            // the slot).
            if (oldContent) {
                data[result.day][result.id].entries = result.entry.entryType == "Session" ? result.entry.entries : oldContent;
            }

            // If a session slot is added, let's update the list of sessions
            if (result.session) {
                this.eventInfo.sessions[result.session.id] = result.session;
            }

        }

        var dfr = $.Deferred();
        $('body').one('timetable_redraw', function() {
            $('body').trigger('timetable_update', self);
            dfr.resolve();
        });
        this.timetableDrawer.redraw();
        return dfr.promise();
    },

    /**
     * updateDay should be used when all the entries for a given day will be changed by the
     * info received in 'update'.
     *
     * update must contain:
     *     update.day: string with a given day, e.g. "20100828"
     *     update.entries: all entries for a given day
     *     update.session: info about the session
     */
    _updateDay: function(update) {
        this._processAutoOps(update);

        var data = this.getData();
        var entries = {};

        entries[update.day] = update.entries;
        extend(data, entries);
        this._removeMissingEntries(update.entries, update.day);

        if (exists(update.session)) {
            this.eventInfo.sessions[update.session.id] = update.session;
        }

        var self = this;
        var dfr = $.Deferred();
        $('body').bind('timetable_redraw', function() {
            dfr.resolve();
            $('body').trigger('timetable_update', self);
        });
        this.timetableDrawer.redraw();
        return dfr.promise();
    },

    _removeMissingEntries: function(entries, day) {
        var self = this;
        _.each(self.data[day], function(value, key) {
            if (!entries[key]) {
                delete self.data[key];
            }
        });
    },

    _updateSessionData: function(sessionId, fields, newValues) {

        var data = this.getData();

        for (var day in data) {
            for (var entry in data[day]) {
                if ( data[day][entry]["entryType"] == "Session" && data[day][entry]["sessionId"] == sessionId ) {
                    for (var i = 0 ; i < fields.length ; ++i) {
                        data[day][entry][fields[i]] = newValues[i];
                    }
                }
            }
        }

        this.timetableDrawer.redraw();
    },

    _getInfoBoxContent: function() {
        return '';
    },

    getTTMenu: function() {
        if (this.isSessionTimetable && this.canManageEvent) {
            var goBackLink = $('<a>', {
                'class': 'icon-arrow-up i-button',
                'href': build_url(Indico.Urls.Timetable.management, {'confId': this.eventInfo.id})
            }).text($T.gettext('Go to event timetable'));
            return $('<div>', {'class': 'group right'}).append(goBackLink);
        } else {
            return null;
        }
    },

    _retrieveHistoryState: function(hash) {
        var dayInterval = this._parseDayInterval(hash);

        var currentDay =  dayInterval[0] || keys(this.data)[0];
        if (dayInterval[1]) {
            this.setSelectedTab(dayInterval[0]);
            this.switchToInterval(dayInterval[1]);
        } else {
            this.switchToTopLevel();
            this.setSelectedTab(dayInterval[0]);
        }
    }
},
     function(data, eventInfo, width, wrappingElement, detailLevel, historyBroker, isSessionTimetable, customLinks,
              canManageSession, canManageBlocks, canManageContribs, canManageEvent) {

         this.isSessionTimetable = isSessionTimetable;
         this.isTopLevel = true;

         this.ManagementTimeTable(data, eventInfo, eventInfo, width, wrappingElement, detailLevel, customLinks, canManageSession, canManageBlocks, canManageContribs, canManageEvent);
         var managementActions = new TopLevelTimeTableManagementActions(this, eventInfo, eventInfo, isSessionTimetable);
         this.TopLevelTimeTableMixin(data, width, wrappingElement, detailLevel, managementActions, historyBroker, 'proportional');

         this.postDraw = TopLevelTimeTableMixin.prototype.postDraw;

     });


type("IntervalManagementTimeTable", ["ManagementTimeTable", "IntervalTimeTableMixin"], {

    _updateTimes: function(newStartTime, newEndTime) {
        this.slotStartTime.set(newStartTime.slice(0,5));
        this.slotEndTime.set(newEndTime.slice(0,5));
    },

    _updateEntry: function(result, oldEntryId, updateCycle) {
        var self = this;
        var slot = this.contextInfo;

        // Delete the old entry
        delete this.parentTimetable.data[this.currentDay][slot.id].entries[oldEntryId];

        this._processAutoOps(result);

        // Here's the update cycle
        if (updateCycle) {
            updateCycle(this.parentTimetable.getData());
        } else {

            if (result.session) {
                // Account for "collateral damage" on sessions
                this.parentTimetable.eventInfo.sessions[result.session.id] = result.session;
            }

            if (exists(result.slotEntry)) {
                // Save the entries, otherwise they are lost
                result.slotEntry.entries = slot.entries;
                this.parentTimetable.data[result.day][result.slotEntry.id] = result.slotEntry;
                this.contextInfo = result.slotEntry;
            }
            this.parentTimetable.data[result.day][slot.id].entries[result.entry.id] = result.entry;

            // Update the times for the slot
            this._updateTimes(result.slotEntry.startDate.time,
                              result.slotEntry.endDate.time);

        }

        var dfr = $.Deferred();
        $('body').one('timetable_redraw', function() {
            $('body').trigger('timetable_update', self);
            dfr.resolve();
        });
        this.timetableDrawer.redraw();
        return dfr.promise();
    },

    /**
     * updateDay should be used when all the entries for a given slot will be changed by the
     * info received in 'update'.
     *
     * update must contain:
     *     update.day: string with a given day, e.g. "20100828"
     *     update.entries: all entries for a given slot
     *     update.slotEntry: info about the slot
     *     update.session: info about the session
     */
    _updateDay: function(update) {
        this._processAutoOps(update);

        var slot = this.contextInfo;
        extend(this.data, update.entries);
        this._removeMissingEntries(update.entries);

        if (exists(update.session)) {
            this.parentTimetable.eventInfo.sessions[update.session.sessionId] = update.session;
        }

        if (exists(update.slotEntry)) {
            // Save the entries, otherwise they are lost
            update.slotEntry.entries = slot.entries;
            this.parentTimetable.data[update.day][update.slotEntry.id] = update.slotEntry;
            this.contextInfo = update.slotEntry;

            // Update the times for the slot
            this._updateTimes(update.slotEntry.startDate.time, update.slotEntry.endDate.time);
        }

        var dfr = $.Deferred();
        $('body').bind('timetable_redraw', function() {
            dfr.resolve();
        });

        this.timetableDrawer.redraw();
        return dfr.promise();
    },

    _removeMissingEntries: function(entries) {
        var self = this;
        _.each(self.data, function(value, key) {
            if (!entries[key]) {
                delete self.data[key];
            }
        });
    },

    getTTMenu: function() {
        var self = this;
        var goBackLink = $('<a class="icon-arrow-up i-button go_back" href="#"/>').text($T('Up to timetable')).
            click(function() {
                self.parentTimetable.switchToTopLevel();
                self._hideWarnings();
                self.session = null;
                return false;
            });

        return $('<div class="group right"/>').append(goBackLink);
    }

},
     function(parent, data, contextInfo, eventInfo, width, wrappingElement, detailLevel, isSessionTimetable, customLinks,
              canManageSession, canManageBlocks, canManageContribs) {
         this.isSessionTimetable = isSessionTimetable;
         this.isTopLevel = false;
         this.ManagementTimeTable(data, contextInfo, eventInfo, width, wrappingElement, detailLevel, customLinks, canManageSession, canManageBlocks, canManageContribs);
         var managementActions = new IntervalTimeTableManagementActions(this, eventInfo, contextInfo, isSessionTimetable);
         this.IntervalTimeTableMixin(parent, width, wrappingElement, managementActions, 'proportional');

         this.canvas = Html.div({});
         this.isPoster = contextInfo.isPoster;

         this.setData = IntervalTimeTableMixin.prototype.setData;
         this.getById = IntervalTimeTableMixin.prototype.getById;
         this.postDraw = IntervalTimeTableMixin.prototype.postDraw;
     });


type("SessionDisplayTimeTable", ["TopLevelDisplayTimeTable"], {

    _functionButtons: function() {
        var self = this;

        this.TopLevelDisplayTimeTable.prototype._functionButtons.call(this);

        return [this.printButton,
                this.fullScreenButton,
                this.filterButton];
    }
},
    function(data, eventInfo, width, wrappingElement, historyBroker) {

        this.TopLevelDisplayTimeTable(data, eventInfo, width, wrappingElement, 'contribution', historyBroker, null);

    });
