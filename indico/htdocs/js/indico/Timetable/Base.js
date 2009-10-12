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

function getTimetableDataById(data, id) {
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
        throw 'not implemented!';
    } else if (type=='SessionSlot'){
        compositeId = ['s'+info[0]+'l'+info[1]];
    } else {
        throw 'unrecognized id!';
    }

    for (day in data) {
        if (data[day][compositeId]) {
            return data[day][compositeId];
        }
    }
}

type("TimeTable", [], {

    /*
     * Translates the keys used in the data dictionary into titles
     * displayed in the tab control
     */

    _draw: function(timetableDiv) {
        return Html.div({style:{width: pixels(this.width)}},
                        this._getHeader(),
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
        return getTimetableDataById(this.data, id);
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

         this.width = width;
         this.loadingIndicator = this._createLoadingIndicator();

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

    layoutMenu: function() {
        var self = this;

        var layoutLink = Html.a({href: '#'}, $T("Layout"));
        this.layoutMenu = new TimetableLayoutMenu(layoutLink, self.timetableDrawer);

        layoutLink.observeClick(function(e) {
            var pos = layoutLink.getAbsolutePosition();
            //              e.preventDefault();
            self.layoutMenu.open(pos.x + layoutLink.dom.offsetWidth, pos.y);
            return false;
        });

        return Html.ul({className: "inner", style: {display: 'block'}},
                       Html.li("menuConfMiddleCell",
                               layoutLink));
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

        var goBackLink = Html.a({href: '#', style: {fontSize: '13pt'}}, 'Go back');
        var printLink = Html.a({href: '#', style: {fontSize: '13pt'}}, 'Print');

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
    _titleTemplate : function(text) {
        if (text == 'all') {
            return $T('All days');
        }

        var day = text.substring(6,8);
        var month = text.substring(4,6);

        var strDate =  day + '/' + month + '/' + text.substring(0,4);

        var nDate = new Date();
        setDate(nDate, parseDate(strDate));

        return Indico.Data.WeekDays[nDate.getDay()].substring(0,3)+' '+day+'/'+month;

    }

},
     function(data, width, wrappingElement, detailLevel) {

         var self = this;

         var canvas = Html.div('canvas');

         this.timetableDrawer = new TimetableDrawer(data, canvas, width,
                                                    wrappingElement,
                                                    detailLevel,
                                                    this._functionButtons(),
                                                    this.loadingIndicator);


         var sortedKeys = keys(this.data);
         sortedKeys.sort();


         var today = new Date();
         var todayStr = IndicoUtil.formatDate2(today);

         var initialTab = -1;
         while (exists(data[todayStr])) {
             today.setDate(today.getDate()-1);
             todayStr = IndicoUtil.formatDate2(today);
             initialTab++;
         }
         // if today not found, set initial tab to the first one
         if (initialTab == -1) {
             initialTab = 0;
         }

         this.LookupTabWidget( translate(sortedKeys, function(key) {
             return [key, function() {
                 self.currentDay = key;
                 // each time one tab is clicked,
                 // drawDay is called over a different day
                 if (key == 'all') {
                     return self._draw(self.timetableDrawer.drawAllDays());
                 } else {
                     return self._draw(self.timetableDrawer.drawDay(key));
                 }
             }];
         }), this.width, 100, initialTab, this._functionButtons());

     });


type("IntervalTimeTableMixin", [], {
},
     function(isSessionTimetable) {

         var canvas = Html.div('canvas');

         this.timetableDrawer = new IntervalTimetableDrawer(data, canvas, width,
                                                            wrappingElement,
                                                            this._functionButtons(),
                                                            this.loadingIndicator,
                                                            managementMode,
                                                            this.managementActions);

         this.isSessionTimetable = any(isSessionTimetable, false);
     });


type("ManagementTimeTable",["TimeTable"], {
    _getHeader: function() {
        var div = this.managementActions.managementHeader(this.isSessionTimetable);
        return div;
    }
},
     function(data, eventInfo, width, wrappingElement, detailLevel) {
         this.eventInfo = eventInfo;
         this.managementActions = new TimetableManagementActions(this, eventInfo);
         this.TimeTable(data, width, wrappingElement, detailLevel, true);
     }
    );


type("TopLevelDisplayTimeTable", ["DisplayTimeTable", "TopLevelTimeTableMixin"], {


},
     function(data, width, wrappingElement, detailLevel) {

         this.DisplayTimeTable(data, width, wrappingElement, detailLevel);
         this.TopLevelTimeTableMixin(data, width, wrappingElement, detailLevel);

         this._filterSetup();

     });


type("IntervalManagementTimeTable", ["ManagementTimeTable", "IntervalTimeTableMixin"], {


},
     function(data, eventInfo, width, wrappingElement, detailLevel, isSessionTimetable) {

         this.IntervalTimeTableMixin(isSessionTimeTable);
         this.ManagementTimeTable(data, eventInfo, width, wrappingElement, detailLevel);

     });

