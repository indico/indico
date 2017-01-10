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

// Filters - User Interface

type("TimetableFilterList", ["CheckPopupWidget"],
     {
         draw: function(x, y) {
             return this.CheckPopupWidget.prototype.draw.call(this, x, y, 300, {position: 'fixed', left: pixels(x), bottom: pixels(y)});
         }
     },
     function(filterName, timetableDrawer, chainElements, noOptionsMessage) {
         var filterObject = TimetableDefaults.filters[filterName].filter;
         var optionStates = filterObject.getOptionStates();
         var optionNames = filterObject.getOptionNames();
         var optionColors = filterObject.getOptionColors();
         var optionTextColors = filterObject.getOptionTextColors();

         optionStates.observe(function() {
             if (!timetableDrawer.preventRedraw)
                 timetableDrawer.setLoading(true, timetableDrawer.redraw);
         });

         this.CheckPopupWidget(optionNames, optionStates, optionColors, optionTextColors, chainElements, noOptionsMessage);
     });

type("TimetableFilterMenu", ["PopupMenu"],
     {
     },

     function(triggerElement, timetableDrawer) {

         var menu = {};
         var self = this;

         // build a dictionary that represents the menu
         each(TimetableDefaults.filters,
              function(value, key) {
                  // each entry will present a list of filters
                  menu[value.name] = new TimetableFilterList(key, timetableDrawer, [triggerElement, self], 'No ' + key + 's found');
              });

         this.PopupMenu(menu, [triggerElement]);
         this.timetableDrawer = timetableDrawer;
     });

// Filter definitions - Core

type("Filter", [],
     {
         getOptionNames: function() {
             return this.options;
         },

         getOptionStates: function() {
             return this.optionStates;
         },

         getOptionColors: function() {
             return this.optionColors;
         },

         getOptionTextColors: function() {
             return this.optionTextColors;
         },

         setData: function(data, day) {
             this.data = data;
             this.day = day;
             this.computeOptions();
         },

         computeOptions: function() {
             var self = this;

             this.options.clear();
             this.optionStates.clear();

             var dayData = this.data[this.day];
             if (this.day == 'all') {
                 each(this.data, function(dayData, day) {
                     each(dayData, function(entryData, entry) {
                         self.processEvent(entryData, entry);
                     });
                 });
             } else {
                 each(dayData, function(entryData, entry) {
                     self.processEvent(entryData, entry);
                 });
             }
         },
         reset: function() {
             var self = this;
             each(this.options, function(value, id) {
                 self.resetEvent(id);
             });
         }

     }, function() {
         this.options = new WatchObject();
         this.optionStates = new WatchObject();
         this.optionColors = new WatchObject();
         this.optionTextColors = new WatchObject();
     });

type("SessionFilter", ["Filter"],
     {
         apply: function(event) {
             var show = true;
             this.optionStates.each(function(value, key) {
                 if (event.entryType == 'Session' && key == event.sessionId) {
                     if (!value) {
                         show = false;
                     }
                 }
             });
             return show;
         },

         processEvent: function(entryData, entry) {
             var self = this;
             if (entryData.entryType == 'Session') {
                 self.options.set(entryData.sessionId, entryData.title);
                 self.optionStates.set(entryData.sessionId, true);
                 self.optionColors.set(entryData.sessionId, entryData.color);
                 self.optionTextColors.set(entryData.sessionId, entryData.textColor);
             }
         },

         resetEvent: function(entry) {
             this.optionStates.set(entry, true);
         }
     },
     function() {
         this.Filter();
     });

type("RoomFilter", ["Filter"],
     {
         apply: function(event) {
             var show = true;
             this.optionStates.each(function(value, key) {
                 if (event.room == key) {
                     if (!value) {
                         show = false;
                     }
                 }
             });
             return show;
         },

         processEvent: function(entryData, entry) {
             var self = this;
             if (exists(entryData.room) && trim(entryData.room) !== '') {
                 self.options.set(entryData.room, entryData.room);
                 self.optionStates.set(entryData.room, true);
             }
         },

         resetEvent: function(entry) {
             this.optionStates.set(entry, true);
         }
     },
     function() {
         this.Filter();
     });

type("TimeTableFilter", ["IWidget"], {
    draw: function() {
        var self = this;

        var content = Html.div('content clearfix');

        var closeButton = Html.div('closeButton');
        closeButton.observeClick(function(e) {
            if (self.closeHandler())
                self.show(false);
        });
        content.append(closeButton);

        this.tableRow = Html.tr();
        content.append(Html.table({cellPadding: 0, cellSpacing: 1, border: 0}, Html.tbody({}, this.tableRow)));

        var sessionsLink = Html.span('dropUpMenu fakeLink', $T('Sessions'));
        var sessionsMenu = new TimetableFilterList('session', self.timetableDrawer, [sessionsLink], $T('No sessions in the timetable'));
        this.setUpFilterMenu(sessionsLink, sessionsMenu);

        var roomsLink = Html.span('dropUpMenu fakeLink', $T('Rooms'));
        var roomsMenu = new TimetableFilterList('room', self.timetableDrawer, [roomsLink], $T('No rooms found in the timetable'));
        this.setUpFilterMenu(roomsLink, roomsMenu);


        this.tableRow.insert(Html.td({style: {width: '90px', color: '#777', fontWeight: 'bold'}}, $T('Filter options')));

        var resetButton = Html.input('button', {style: {cssFloat: 'right', marginRight: '50px'}}, $T('Reset filter'));
        resetButton.observeClick(function() {
            each(TimetableDefaults.filters, function(TTfilter) {
                TTfilter.filter.reset()
            });
        });

        this.tableRow.append(Html.td({style: {width: 'auto'}}, resetButton));

        this.div.append(content);

        this.height = $(self.div.dom).height();

        // Hide it by default
        this.div.dom.style.display = 'none';
    },
    setUpFilterMenu: function (link, menu)
    {
        var self = this;

        this.tableRow.append(Html.td({}, link));

        link.observeClick(function() {
            if (menu.active) {
                menu.close();
                return;
            }
            var pos = link.getAbsolutePosition();
            menu.open(pos.x - 30, self.height);
        });
    },
    show: function(show) {
        this.state.set(!this.state.get());
        if (show)
            $(this.div.dom).show("slide", { direction: "down" }, 200);
        else
            $(this.div.dom).hide("slide", { direction: "down" }, 200);
    },
    toggle: function() {
        this.show(!this.state.get())
    }
    },
    function(timetableDrawer, closeHandler) {
        var self = this;

        this.timetableDrawer = timetableDrawer;
        this.closeHandler = closeHandler;

        this.state = new WatchValue(false);

        this.div = Html.div({className: 'timetableFilter', style: {display: "none"}});
        $E(document.body).append(this.div);
    }
);
