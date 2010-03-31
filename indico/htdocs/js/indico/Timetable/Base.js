var TimetableDefaults = {
    topMargin: 30,
    bottomMargin: 40,
    leftMargin: 55,
    rightMargin: 5,
    resolution: 1,
    menuWidth: 150,
    blockMargin: 4,         // Margin used inside timetable blocks
    wholeDay : 7,              // # of hours of duration for a timetable event to be seen as be during the whole day.
    minContribHeight: 20,      // Minimum height for a contrib displayed inside a session TODO: remove?
    layouts: {'compact': {name: "Compact",
                          values : {
                              pxPerHour: 60,
                              pxPerSpace: 2,
                              minPxPerBlock: 50
                          },
                          manager: new CompactLayoutManager()},

              'proportional': {name: 'Proportional',
                               values : {
                                   pxPerHour: 50,
                                   minPxPerBlock: 25
                               },
                               manager: new ProportionalLayoutManager()
                              },

              'poster': {name: 'Poster',
                         manager: new PosterLayoutManager()
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

        return Html.div({style:{width: this.width}},
                        this.header,
                        timetableDiv,
                        this.loadingIndicator);
    },

    _getMenu: function() {
        return Html.div();
    },

    postDraw: function() {
        this.timetableDrawer.postDraw();
        this.LookupTabWidget.prototype.postDraw.call(this);
    },

    getData: function() {
        return this.data;
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

        for (day in this.data) {
            if (this.data[day][compositeId]) {
                return this.data[day][compositeId];
            }
        }
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
      * To be overloaded. Returns buttons to be displayed below the tabs in
      * the tab widget.
      */
    _functionButtons: function() {
        return [];
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

        //self.timetableDrawer.setPrintableVersion(true);

        var bodyPadding = $E(document.body).dom.style.padding;
        var timetableElements = translate(self.timetableDrawer.canvas.dom.childNodes, function(value) {return $E(value);});
        var elements = translate($E(document.body).dom.childNodes, function(value) {return $E(value);});

        var goBackLink = Html.a({href: '#', style: {fontSize: '17px'}}, 'Go back');
        var printLink = Html.a({href: '#', style: {fontSize: '17px'}}, 'Print');

        var links = Html.span({style: {cssFloat: 'right'}}, printLink, ' | ', goBackLink);

        var headerStyle = {padding: '0px 5px 5px 5px',
            borderBottom: '1px solid black',
            textAlign: 'center',
            width: pixels(self.timetableDrawer.width)};
        var header = Html.div({className: 'timetableHeader clearfix', style: headerStyle}, links,
            Html.span({style: {cssFloat: 'left'}}, self._titleTemplate(self.timetableDrawer.day)));

        goBackLink.observeClick(function(e) {
            self.timetableDrawer.setPrintableVersion(false);
            $E(document.body).setStyle('padding', bodyPadding);
            $E(document.body).set(elements);

        });
        printLink.observeClick(function(e) {
            window.print();
        });
        var timetableDiv = Html.div({style: {paddingTop: pixels(20), position: 'relative'}}, timetableElements);
        $E(document.body).set(header, timetableDiv);
        $E(document.body).setStyle('padding', pixels(30));
    },

    _filterSetup: function() {
        var self = this;
        this.filter = new TimeTableFilter(this.timetableDrawer, function () {
            // When closed restore the filter button color
            self.filterButtonContainer.dom.style.background = "";
            return true;
        });
        this.filter.draw();
    },

    _functionButtons: function() {
        var self = this;

        var printButton = {'btn': Html.div('printButtonWhite', $T('Print')),
            'onclick': function(btnContainer) {
                self.print();
            }
                          };

        // TODO: Needs to be implemented
        var linkButton = Html.div('linkButtonWhite', $T('Link'));

        var detailsButton = {'btn': Html.div('buttonWhite', Html.span({}, $T('Detailed view'))),
            'onclick': function(btnContainer) {
                var detailLevel = self.timetableDrawer.detail.get();
                var newDetailLevel = detailLevel == 'contribution' ? 'session' : 'contribution';
                self.timetableDrawer.detail.set(newDetailLevel);
                var state = (newDetailLevel == 'contribution');
                //detailsButton.btn.set(state ? "Hide details" : "Show details");
                btnContainer.dom.style.background = state ? "#9F883B" : "";
            }};

        var filterButton = {'btn': Html.div('buttonWhite', $T('Filter')),
            'onclick': function(btnContainer) {
                // Save the container so that the filter button background
                // color can be restored when filter is closed
                self.filterButtonContainer = btnContainer;
                self.filter.toggle();
                var state = self.filter.state.get();
                btnContainer.dom.style.background = state ? "#9F883B" : "";
            }
                           };

        return [printButton,
                detailsButton,
                filterButton];
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


type("TopLevelTimeTableMixin", ["LookupTabWidget"], {

    draw: function() {

        return this.LookupTabWidget.prototype.draw.call(this);
    },

    getDays: function() {
        return this.sortedKeys;
    },

    disable: function() {
        this.enabled = false;
        this.LookupTabWidget.prototype.disable.call(this);
    },

    enable: function() {
        this.enabled = true;
        this.LookupTabWidget.prototype.enable.call(this);
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
        var m = hash.match(/#(\d{8})(?:\.(s\d+l\d+))?/);

        if (m) {
            return [m[1],m[2]];
        } else {
            return [null, null];
        }
    },

    switchToInterval : function(intervalId) {
        this.disable();

        var intervalInfo = this.data[this.currentDay][intervalId];
        var data = intervalInfo.entries;

        this.intervalTimeTable = new IntervalManagementTimeTable(this,
                                                                 data,
                                                                 intervalInfo,
                                                                 this.eventInfo,
                                                                 this.width.slice(0,-2),
                                                                 this.canvas,
                                                                 'contribution',
                                                                this.isSessionTimetable);

        this.intervalTimeTable.setData(intervalInfo);
        var content = this.intervalTimeTable.draw()
        this.canvas.set(content);
        this.menu.dom.style.display = 'none';

    },

    postDraw: function() {
        this.TimeTable.prototype.postDraw.call(this);
        var self = this;

    },

    switchToTopLevel : function() {
        this.enable();
        this.setSelectedTab(this.currentDay);
        this._drawContent();
        this.menu.dom.style.display = 'block';
        this.timetableDrawer.redraw();
    }

},
     function(data, width, wrappingElement, detailLevel, managementActions, historyBroker) {

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
                                                    managementActions);

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
                 // otherwise use the default
                 initialTab = keys(data)[0];
             }
         }

         this.currentDay = initialTab;

         this.LookupTabWidget( translate(this.sortedKeys, function(key) {

             return [key, function() {
                 self.currentDay = key;
                 // each time one tab is clicked,
                 // drawDay is called over a different day
                 if (key == 'all') {
                     self._addToHistory('all');
                     return self._draw(self.timetableDrawer.drawAllDays());
                 } else {

                     // Are we switching to interval mode
                     if (!self.enabled) {
                         // stop everything, we don'w want the LookupTabWidget
                         // to replace the contents
                         throw "stopDrawing";
                     }

                     self._addToHistory(key);
                     return self._draw(self.timetableDrawer.drawDay(key));
                 }
             }];
         }), this.width, 100, initialTab, this._functionButtons(), this.canvas);

         if (dayAndInterval[1]) {
             // TODO: replace with appropriate notification system
             setTimeout(function() {
                 self.switchToInterval(dayAndInterval[1]);
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
            $T('You are viewing the contents of the interval:')),
            Html.div({style: {fontWeight: 'bold', marginTop: '5px', fontSize: '1.3em'}},
            this._generateSlotTitle(this.contextInfo),
            Html.span({style: {fontWeight: 'normal'}},
            " (", $B(Html.span({}), this.slotStartTime), " - ", $B(Html.span({}), this.slotEndTime),")" )));
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
     function(parent, width, wrappingElement, managementActions) {

         this.managementActions = managementActions;
         this.parentTimetable = parent;

         this.timetableDrawer = new IntervalTimetableDrawer(this, width,
                                                            wrappingElement,
                                                            this._functionButtons(),
                                                            this.loadingIndicator,
                                                            !!managementActions,
                                                            managementActions);
     });


type("ManagementTimeTable",["TimeTable"], {

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
                                       Conference: $T('The <strong>starting time</strong> of the <strong>Conference</strong> was moved from ')
                                   },
                                   OWNER_END_DATE_EXTENDED: {
                                       SessionSlot : $T('The <strong>ending time</strong> of the session interval <strong>') + title + $T('</strong> was moved from '),
                                       Session: $T('The <strong>ending time</strong> of the session interval <strong>') + title + $T('</strong> was moved from '),
                                       Conference: $T('The <strong>ending time</strong> of the <strong>Conference</strong> was moved from ')
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

        var slot = null;
        var title = "";

        var startTime = "";
        var endTime = "";

        if (type == "Session") {
            return null;
        } else if (type == 'Conference') {
            conference = self.timetable.getById(entry[2]);
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


    _getHeader: function() {

        var self = this;

        this.infoBox = Html.div({className: 'timetableInfoBox'});

        this.addMenuLink = Html.a({className: 'dropDownMenu fakeLink', style: {margin: '0 15px'}}, 'Add new');

        this.addMenuLink.observeClick(function() {
            self.managementActions._openAddMenu(self.addMenuLink, self.contextInfo);
        });

        this.separator = Html.span({}, " | ");

        this.rescheduleLink = Html.span({className: 'fakeLink', style:{paddingLeft: pixels(15), paddingRight: pixels(15)}}, $T('Reschedule'));
        this.rescheduleLink.observeClick(function(){
            var popup = new RescheduleDialog(self);
            popup.open();
        });

        // JUST FOR SessionManagementTimetable
        this.addIntervalLink = Html.span({className: 'fakeLink', style:{paddingLeft: pixels(15), paddingRight: pixels(15)}}, $T('Add new interval'));
        this.separator2 = Html.span({}, " | ");
        this.fitInnerTimetableLink = Html.span({className: 'fakeLink', style:{paddingLeft: pixels(15), paddingRight: pixels(15)}}, $T('Fit inner timetable'));


        if (self.isSessionTimetable) {
            this.addIntervalLink.observeClick(function() {
                self.managementActions.addSessionSlot(self.eventInfo.timetableSession);
            });
            this.fitInnerTimetableLink.observeClick(function(){
                var popup = new FitInnerTimetableDialog(self);
                popup.open();
            });
        }

        this.warningArea = this._createInfoArea();
        this.warningArea.dom.style.display = 'none';

        this.menu = Html.div({style: {cssFloat: 'right', color: '#777'}},
                             this.getTTMenu(),
                             this.addMenuLink,
                             this.addIntervalLink,
                             this.separator,
                             this.rescheduleLink,
                             this.separator2,
                             this.fitInnerTimetableLink);
        return Html.div({}, this.warningArea, Html.div('clearfix', this.menu, this.infoBox));
    }
},
     function(data, contextInfo, eventInfo, width, wrappingElement, detailLevel) {
         this.eventInfo = eventInfo;
         this.contextInfo = contextInfo;
         this.warnings = new WatchList();

         this.TimeTable(data, width, wrappingElement, detailLevel, true);

     }
    );


type("TopLevelDisplayTimeTable", ["DisplayTimeTable", "TopLevelTimeTableMixin"], {

    _retrieveHistoryState: function(hash) {
        var currentDay = this._parseDayInterval(hash)[0];
        this.setSelectedTab(currentDay);
    }


},
     function(data, contextInfo, width, wrappingElement, detailLevel, historyBroker) {

         this.DisplayTimeTable(data, width, wrappingElement, detailLevel);
         this.TopLevelTimeTableMixin(data, width, wrappingElement, detailLevel, null, historyBroker);

         this.eventInfo = contextInfo;

         this._filterSetup();

         this.postDraw = TopLevelTimeTableMixin.prototype.postDraw;

     });

type("TopLevelManagementTimeTable", ["ManagementTimeTable", "TopLevelTimeTableMixin"], {

    _deleteOldEntry: function(data, result, oldEntryId) {
        /*
         * Deletes the old version of the entry
         */

        var oldStartTime, oldEndTime, oldStartDate;
        // Check whether we're operating *over* an existing slot or not
        // it is a slot && slot exists in timetable
        if (result.entry.entryType=="Session" && data[this.currentDay][result.id]) {
            var slot = data[this.currentDay][result.entry.id];
            //var slot = data[result.day][result.entry.id];
            // in the affirmative case, fetch the time limits
            oldStartTime = slot.startDate.time.slice(0,5);
            oldEndTime = slot.endDate.time.slice(0,5);
            oldStartDate = slot.startDate.date.replaceAll('-','');

        } else {
            // Contribution or break - event timetable limits

            var entry = data[result.day][result.entry.id];

            oldStartTime = this.eventInfo.startDate.time.slice(0,5);
            oldEndTime = this.eventInfo.endDate.time.slice(0,5);
            oldStartDate = this.currentDay;
        }

        var oldEntries = data[oldStartDate][oldEntryId]?data[oldStartDate][oldEntryId].entries:null;

        delete data[oldStartDate][oldEntryId];

        return oldEntries;

    },

    _updateEntry: function(result, oldEntryId, updateCycle) {

        var data = this.getData();

        // AutoOp Warnings (before updates are done)
        this._processAutoOps(result);

        // Deletes the old version of the entry
        var oldEntries = this._deleteOldEntry(data, result, oldEntryId);

        // Here's the update cycle
        if (updateCycle) {
            updateCycle(data);
        } else {

            // If none is defined in the function args,
            // execute the default action
            data[result.day][result.id] = result.entry;

            // A session interval may contain entries, that
            // should be preserved
            if (oldEntries) {
                data[result.day][result.id].entries = oldEntries;
            }

            // If a session slot is added, let's update the list of sessions
            if (result.session) {
                this.eventInfo.sessions[result.session.id] = result.session;
            }

        }

        // Check if the result overflows the conference ending time
        if ((result.day == this.eventInfo.endDate.date.replaceAll('-','')) &&
            (result.entry.endDate.time.replaceAll(':','') >
             this.eventInfo.endDate.time.replaceAll(':',''))) {
            this.eventInfo.endDate.time = result.endTime;
        }

        this.timetableDrawer.redraw();
    },

    _updateDay: function(result) {

        this._processAutoOps(result);

        var data = this.getData();

        var entry = {};
        entry[result.id] = result.entry;

        extend(data, entry);

        this.timetableDrawer.redraw();
    },

    _updateMovedEntry: function(result, oldEntryId) {
        this._updateEntry(result, oldEntryId, function(data){
            if (exists(result.slotEntry)) {
                // move into a session slot
                data[result.day][result.slotEntry.id].entries[result.id] = result.entry;
                // updates the time of the session if it has to be extended
                data[result.day][result.slotEntry.id].startDate.time = result.slotEntry.startDate.time;
                data[result.day][result.slotEntry.id].endDate.time = result.slotEntry.endDate.time;
            } else {
                data[result.day][result.id] = result.entry;
            }
        });
    },

    _getInfoBoxContent: function() {
        return '';
    },

    getTTMenu: function() {

        if (this.isSessionTimetable) {
            this.addMenuLink.dom.style.display = "none";
            this.addIntervalLink.dom.style.display = "inline";
            this.rescheduleLink.dom.style.display = "none";
            this.separator.dom.style.display = "none";
        } else {
            this.addIntervalLink.dom.style.display = "none";
            this.separator2.dom.style.display = "none";
            this.fitInnerTimetableLink.dom.style.display = "none";
        }

        return '';
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
     function(data, eventInfo, width, wrappingElement, detailLevel, historyBroker, isSessionTimetable) {

         this.isSessionTimetable = isSessionTimetable;

         this.ManagementTimeTable(data, eventInfo, eventInfo, width, wrappingElement, detailLevel);
         var managementActions = new TopLevelTimeTableManagementActions(this, eventInfo, eventInfo, isSessionTimetable);
         this.TopLevelTimeTableMixin(data, width, wrappingElement, detailLevel, managementActions, historyBroker);

         this.postDraw = TopLevelTimeTableMixin.prototype.postDraw;

     });


type("IntervalManagementTimeTable", ["ManagementTimeTable", "IntervalTimeTableMixin"], {

    _updateTimes: function(newStartTime, newEndTime) {
        this.slotStartTime.set(newStartTime.slice(0,5));
        this.slotEndTime.set(newEndTime.slice(0,5));
    },

    _updateEntry: function(result, oldEntryId, updateCycle) {

        var slot = this.contextInfo;
        var data = this.getData();

        // Delete the old entry
        delete this.parentTimetable.data[this.currentDay][slot.id].entries[oldEntryId];

        this._processAutoOps(result);

        // Here's the update cycle
        if (updateCycle) {
            updateCycle(this.parentTimetable.getData());
        } else {

            // If none is defined in the function args,
            // execute the default action
            data[result.id] = result.entry;

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

        this.timetableDrawer.redraw();

    },

    _updateMovedEntry: function(result, oldEntryId) {
        this._updateEntry(result, oldEntryId, function(data){
            if(exists(result.slotEntry)){
                // from slot to slot
                data[result.day][result.slotEntry.id].entries[result.id] = result.entry;
                // updates the time of the session if it has to be extended
                data[result.day][result.slotEntry.id].startDate.time = result.slotEntry.startDate.time;
                data[result.day][result.slotEntry.id].endDate.time = result.slotEntry.endDate.time;
            } else {
                // from slot to top level
                data[result.day][result.id]=result.entry;
            }
        });
    },

    _updateDay: function(result) {

        this._processAutoOps(result);

        var data = this.getData();

        extend(data, result.entry);

        this.timetableDrawer.redraw();
    },

    getTTMenu: function() {
        var self = this;

        this.separator2.dom.style.display = "none";
        this.fitInnerTimetableLink.dom.style.display = "none";
        if (this.isSessionTimetable) {
            this.addMenuLink.dom.style.display = "inline";
            this.addIntervalLink.dom.style.display = "none";
            this.rescheduleLink.dom.style.display = "none";
            this.separator.dom.style.display = "inline";
        } else {
            this.addIntervalLink.dom.style.display = "none";
        }

        var goBackLink = Html.span({}, Html.a({className: 'fakeLink', style: {fontWeight: 'bold', margin: '0 15px'}}, 'Go back to timetable'), ' | ');
        goBackLink.observeClick(function() {
            self.parentTimetable.switchToTopLevel();
            self._hideWarnings();
            self.session = null;

        });

        return goBackLink;

    }

},
     function(parent, data, contextInfo, eventInfo, width, wrappingElement, detailLevel, isSessionTimetable) {

         this.ManagementTimeTable(data, contextInfo, eventInfo, width, wrappingElement, detailLevel);
         var managementActions = new IntervalTimeTableManagementActions(this, eventInfo, contextInfo, isSessionTimetable);
         this.IntervalTimeTableMixin(parent, width, wrappingElement, managementActions);

         this.canvas = Html.div({});


         this.setData = IntervalTimeTableMixin.prototype.setData;
         this.getById = IntervalTimeTableMixin.prototype.getById;

     });

type("SessionManagementTimeTable", ["TopLevelManagementTimeTable"], {

},
     function(data, eventInfo, width, wrappingElement, historyBroker) {

         this.TopLevelManagementTimeTable(data, eventInfo, width, wrappingElement, 'session', historyBroker, true);
     });
