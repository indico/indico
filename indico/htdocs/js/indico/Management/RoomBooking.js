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

function roomListNothing(data, func) {
    each(data, function() {
        func(true);
    });
}

type("RoomBookingWidget", ["IWidget"],

     {

         _favoriteDecorator: function(key, elem){
             var li = Html.li(this.eventFavorites.indexOf(key)===null?'bottomLine':
                            'bottomLine favoriteItem', elem);

             if (key == this.lastFavorite) {
                 li.dom.style.borderBottom = '1px solid #909090';
             }

             return li;
         },

         _favoriteSort: function(e1, e2){
             if (this.eventFavorites.indexOf(e1) !== null &&
                 this.eventFavorites.indexOf(e2) === null) {
                 return -1;
             } else if (this.eventFavorites.indexOf(e1) === null &&
                        this.eventFavorites.indexOf(e2) !== null) {
                 return 1;
             } else {
                 return SortCriteria.DashSeparated(e1, e2);
             }
         },

         postDraw: function() {
             if(this.defaultLocation != null) {
                 if (this.locationChooser.get() != this.defaultLocation) {
                     this.locationChooser.set(this.defaultLocation);
                 }
             }
             if (this.parentInfo) {
                 this.inheritCheckbox.set(this.inheritDefault);
             }
         },

         draw: function() {

             var rbActive = Indico.Settings.RoomBookingModuleActive;

             this.inheritText = this.parentInfo?Html.span(
                 {},
                 $T('Inherit from parent {0}: ').format(this.parentName),
                 Html.span({},
                           any(this.parentInfo.get('room'), $T('No room defined')) + " (" +
                           any(this.parentInfo.get('location'), $T('No location defined')) + ")")):'';

                 return Html.div(
                         'roomWidget',
                              Html.div({style:{width:425}},
                                  Html.div({style:{paddingTop:'10px', cssFloat: 'left'}},
                                     Html.div('roomWidgetTitle', $T("Location")),
                                     Html.div({}, this.locationChooser.draw())),
                                  Html.div({style:{paddingTop:'10px', paddingLeft:'10px', cssFloat: 'left'}},
                                      Html.div('roomWidgetTitle', $T("Room")),
                                      Html.div({style: {cssFloat:'left'}},
                                                          rbActive ?
                                                          this.roomChooser.draw() :
                                                          this.roomChooser))),
                             Html.div({style:{paddingTop:'10px', clear:'left'}},
                                      this.parentInfo?this.inheritCheckbox:'', this.inheritText),
                             Html.div({style:{paddingTop:'10px', clear:'left'}},
                                     Html.div({className: 'roomWidgetTitle', style: {width: '210px'}}, $T('Address')),
                                     this.addressArea.draw())
                             );


         },

         _startBind: function() {

             if (this.oldInfo) {
                 this.info.update(this.oldInfo.getAll());
             }
             $B(this.locationChooser, this.info.accessor('location'));
             $B(this.roomChooser, this.info.accessor('room'));
             $B(this.addressArea, this.info.accessor('address'));
         },

         _endBind: function() {

             bind.detach(this.locationChooser);
             bind.detach(this.roomChooser);
             bind.detach(this.addressArea);
         },

         _loadRooms: function(newLocation) {

             var cacheEntry = this.roomCache[newLocation];

             if (this.loading){
                 // do nothing
             }
             else if (cacheEntry) {
                 this.roomChooser.setOptionList(cacheEntry);
                 this.roomChooser.setLoading(false);
             } else {
                 var self = this;
                 indicoRequest('roomBooking.rooms.fullNameList',
                               {'location': newLocation},
                               function(result, error) {
                                   self.loading = false;
                                   if (!error) {
                                       var dict = {};

                                       each(result, function(value) {
                                           dict[value[0]] = value[1];
                                       });

                                       self.roomCache[newLocation] = dict;
                                       self.roomChooser.setOptionList(dict);
                                       self.roomChooser.setLoading(false);
                                   } else {
                                       IndicoUtil.errorReport(error);
                                       self.roomChooser.setLoading(false);
                                   }

                               });
                 this.loading = true;
             }

         }
     },
     function(locations, info, parent, inheritDefault, eventFavorites, defaultLocation, parentName) {
         var self = this;
         var rbActive = Indico.Settings.RoomBookingModuleActive;

         this.defaultLocation = defaultLocation;
         this.parentName = parentName || '';
         this.locationChooser = new FlexibleSelect(locations, 177);

         if ( rbActive ) {
             this.roomChooser = new FlexibleSelect(
                 {}, 177,
                 function(e1, e2){
                     return self._favoriteSort(
                         self.roomChooser.list.get(e1),
                         self.roomChooser.list.get(e2));
                 },
                 function(key, elem){
                     return self._favoriteDecorator(key, elem);
                 });
         }
         else {
             this.roomChooser = Html.input('text', {className: "roomTextField",
                                                    name: "_roomName"});
         }

         this.addressArea = new RealtimeTextArea({});
         this.inheritCheckbox = Html.checkbox({});
         this.info = info;
         this.parentInfo = parent;
         this.roomCache = {};
         this.inheritDefault = inheritDefault;
         //this.eventFavorites = $L(eventFavorites || []);
         this.eventFavorites = $L([]);

         // compute last favorite
         var fav = $L(this.eventFavorites.allItems());
         fav.sort(SortCriteria.Integer);
         this.lastFavorite = fav.item(fav.length.get() - 1);

         if (this.parentInfo) {
             this.inheritCheckbox.observe(function(value) {
                 if (value) {
                     self.inheritText.dom.className = 'enhanced';
                     self.locationChooser.disable();
                     if ( rbActive ) {
                        self.roomChooser.disable();
                     }
                     self.addressArea.disable();

                     self.oldInfo = $O(self.info.getAll());
                     self.locationChooser.set(self.parentInfo.get('location'));
                     self.roomChooser.set(self.parentInfo.get('room'));

                     self._endBind();

                     self.info.set('location', null);
                     self.info.set('room', null);
                     self.info.set('address', null);

                 } else {
                     self.inheritText.dom.className = '';
                     self.locationChooser.enable();
                     if ( rbActive ) {
                        self.roomChooser.enable();
                     }
                     self.addressArea.enable();

                     self._startBind();
                 }
             });
         }

         this.locationChooser.observe(function(value){
             if (rbActive && value !== '' && locations !== null) {
                 if (locations[value]) {
                     self.roomChooser.setLoading(true);
                     self._loadRooms(value);
                 } else {
                     self.roomChooser.setOptionList({});
                 }
                 self.roomChooser.set('');
             }
         });

         this._startBind();
     });

type("RoomBookingReservationWidget", ["RoomBookingWidget"],
        {
            _convertDate: function(date) {
                var result;

                if(date.split("/")[0].length != 4){
                    //converting from dd-mm-yyyy to yyyy-mm-dd
                    var monthCorrection = date.split("/")[1].length == 1?"0":"";
                    var dayCorrection = date.split("/")[0].length == 1?"0":"";
                    result = date.split("/")[2] + "-" + monthCorrection + date.split("/")[1] + "-" + dayCorrection + date.split("/")[0];
                }
                else
                    result = date.replace(/[/]/g,"-");
                return result;
            },

            _convertTime: function(sTime) {
                var sTimeCorrection = sTime.length==4?"0":"";
                return sTimeCorrection + sTime + ":00";
            },

            _calculateEndTime: function(sTime, duration) {
                var eHours = parseInt(sTime.split(":")[0],10);
                var eMinutes = parseInt(sTime.split(":")[1],10);
                eHours += parseInt((eMinutes + duration) / 60);
                eMinutes = (eMinutes + duration) % 60;

                eHours = eHours >= 10?eHours:("0" + eHours);
                eMinutes = eMinutes >= 10?eMinutes:("0" + eHours);

                return  eHours + ":" + eMinutes + ":00";
            },

            _getDateTime: function(){
                if( this.dateTime.accessor('startDate').get() && this.dateTime.accessor('duration').get() ) {
                    var sDate = this.dateTime.accessor('startDate').get();
                    var duration = parseInt(this.dateTime.accessor('duration').get());

                    this.date = this._convertDate(sDate.split(" ")[0]);
                    this.sTime = this._convertTime(sDate.split(" ")[1]);
                    this.eTime = this._calculateEndTime(sDate.split(" ")[1], duration);
                } else if( this.dateTime.accessor('startDateTime').get() && this.dateTime.accessor('endDateTime').get()){
                    var sDate = this.dateTime.accessor('startDateTime').get();
                    var eDate = this.dateTime.accessor('endDateTime').get();

                    this.date = this._convertDate(sDate.split(" ")[0]);
                    this.sTime = this._convertTime(sDate.split(" ")[1]);
                    this.eTime = this._convertTime(eDate.split(" ")[1]);
                } else if ( this.dateTime.accessor('date').get() && this.dateTime.accessor('startTime').get() && this.dateTime.accessor('endTime').get() ) {
                    this.date = this.dateTime.accessor('date').get();
                    this.sTime = this._convertTime(this.dateTime.accessor('startTime').get());
                    this.eTime = this._convertTime(this.dateTime.accessor('endTime').get());
                }
            },

            _isOverlapping: function(start, end) {
                if(start.length == 7)
                    start = "0" + start;
                if(end.length == 7)
                    end = "0" + end;

                return (this.sTime > start && this.sTime < end) ||
                       (this.eTime > start && this.eTime < end) ||
                       (this.sTime <= start && this.eTime >= end) ||
                       (this.sTime >= start && this.eTime <= end);
            },

            _isInsideBooking: function(elem) {
                var insideBooking = false;
                for(var resvId in this.bookedRooms.get(elem)){
                    var resv = this.bookedRooms.get(elem)[resvId];
                    if( this.sTime >= resv.startDateTime.time && this.eTime <= resv.endDateTime.time && this.date == resv.startDateTime.date){
                        insideBooking = true;
                        break;
                    }
                }
                return insideBooking
            },

            _findConflict: function(key) {
                var conflict = null;

                this._getDateTime();
                var day = this.timetableData[this.date.replace(/-/g,"")];

                for( var event in day ){
                    if ( event != this.editedEvent){
                        if( !(day[event].entries && day[event].entries[this.editedEvent]) && key == day[event].room && this._isOverlapping(day[event].startDate['time'], day[event].endDate['time'])){
                            conflict = day[event];
                            break;
                        }
                        for(var entry in day[event].entries)
                            if ( entry != this.editedEvent && key == day[event].entries[entry].room && this._isOverlapping(day[event].entries[entry].startDate['time'], day[event].entries[entry].endDate['time'])){
                                conflict = day[event].entries[entry];
                                break;
                            }
                        if( conflict )
                            break;
                    }
                }
                return conflict
            },

            _favoriteDecorator: function(key, elem){
                var li;
                if( this.bookedRooms.get(elem) ){
                    if( this.timetableData) {
                        var conflict = this._findConflict(key);
                        if( !conflict ){
                            if(this._isInsideBooking(elem))
                                li = Html.li('bottomLine bookedItem', elem);
                            else{
                                var infoDiv = Html.div({}, $T("This room is booked for this conference during"));
                                for(var resvId in this.bookedRooms.get(elem)){
                                    var resv = this.bookedRooms.get(elem)[resvId];
                                    infoDiv.append(Html.br());
                                    infoDiv.append(resv.startDateTime.time.substring(0,5) + " - " + resv.endDateTime.time.substring(0,5) + " at "+ resv.startDateTime.date)
                                }
                                li = Html.div({className: 'bookedItemCollisionDiv'},Html.li('bottomLine bookedItemOutsideBooking', elem),infoDiv);
                            }
                        }
                        else {
                            var info = "This room is already used by " + conflict.title + " between " + conflict.startDate['time'].substring(0,5) + " and " + conflict.endDate['time'].substring(0,5) + ".";
                            li = Html.div({className: 'bookedItemCollisionDiv'},Html.li('bottomLine bookedItemCollision', elem),Html.div({},info));
                        }
                    }
                    else{
                        li = Html.li('bottomLine', elem);
                    }
                    if(!this.previousElementBooked) {
                        li = Html.div({},Html.div('bottomLine bookedItemHeader', 'Your booked rooms:'), li);
                        this.previousElementBooked = true
                    }

                }
                else {
                    li = Html.li('bottomLine', elem);
                    if(this.previousElementBooked) {
                        li = Html.div({}, Html.div('bottomLine bookedItemHeader','Other rooms:'), li);
                        this.previousElementBooked = false
                    }
                }
                 return li;
             },

             _favoriteSort: function(e1, e2){
                 this.previousElementBooked = false;
                 if (this.bookedRooms.get(e1) &&
                     !this.bookedRooms.get(e2)) {
                     return -1;
                 } else if (!this.bookedRooms.get(e1) &&
                            this.bookedRooms.get(e2)) {
                     return 1;
                 } else {
                     return SortCriteria.Integer(e1, e2);
                 }
             },

             setDateTimeInfo: function(info) {
                 this.dateTime = info;
             }
        },
        function(locations, info, parent, inheritDefault, eventFavorites, defaultLocation, bookedRooms, timetableData, dateTime, editedEvent, parentName){

            this.RoomBookingWidget(locations, info, parent, inheritDefault, [], defaultLocation, parentName);
            this.bookedRooms = $D(bookedRooms || {} );
            this.dateTime = dateTime;
            this.timetableData = timetableData;
            this.editedEvent = editedEvent;

        });

type("RoomBookingVerticalReservationWidget", ["RoomBookingReservationWidget"],
        {
            draw: function() {
                var rbActive = Indico.Settings.RoomBookingModuleActive;

                this.inheritText = this.parentInfo?Html.span(
                    {},
                    $T('Inherit from parent {0}: ').format(this.parentName),
                    Html.span({},
                              this.parentInfo.get('room') + " (" +
                              this.parentInfo.get('location') + ")")):'';
                    return Html.div(
                            'roomWidget',
                                 Html.div({style:{paddingTop:'5px', clear:'left'}},
                                    Html.div('roomVerticalWidgetTitle', $T("Location")),
                                    Html.div({style: {cssFloat:'left'}}, this.locationChooser.draw())),
                                    Html.div({style:{paddingTop:'5px'}},
                                        Html.div('roomVerticalWidgetTitle', $T("Room")),
                                        Html.div({style: {cssFloat:'left'}},
                                                            rbActive ?
                                                            this.roomChooser.draw() :
                                                            this.roomChooser)),
                                Html.div({style:{paddingTop:'5px', clear:'left'}},
                                         this.parentInfo?this.inheritCheckbox:'', this.inheritText)
                                );
            }

        },
        function(locations, info, parent, inheritDefault, eventFavorites, defaultLocation, bookedRooms, timetableData, dateTime, editedEvent, parentName){
            this.RoomBookingReservationWidget(locations, info, parent, inheritDefault, eventFavorites, defaultLocation, bookedRooms, timetableData, dateTime, editedEvent, parentName);
        });



type("RoomListWidget", ["ListWidget"],
    {
        _drawItem: function(room) {
            var self = this;
            var roomData = room.get();

            var removeButton = Widget.link(command(function() {
                self.removeProcess(room.key, function(result) {
                    if (result) {
                        self.set(room, null);
                    }
                });
            }, IndicoUI.Buttons.removeButton()));
            return Html.div({style:{display: 'inline'}},
                            Html.span({},
                                    Html.div({style: {cssFloat: "right", paddingRight: "10px"}},removeButton),
                                    $B(Html.span(), self.useValue ? roomData : room.key)
                                    ));
        }
    },

    function(style, removeProcess, useValue) {
        this.removeProcess = removeProcess;
        this.useValue = useValue || false;
        if (!exists(style)) {
            style = "UIPeopleList";
        }
        this.ListWidget(style);
    }
);

/**
 * Creates a form field with a list of rooms.
 * Rooms can be added from an initial list of rooms or from a 'Add Room' button.
 */
type("RoomListField", ["IWidget"], {

    getRoom: function() {
        return $L(this.roomList);
    },

    clear: function() {
        this.roomList.clearList();
    },

    draw: function() {

        var self = this;

        var chooserDiv = Html.div({style:{marginTop: pixels(10)}});
        var callback = function(){
            chooserDiv.set(roomChooser.draw(),addRoomButton);
        };

        if(this.allowNew) {
            var roomChooser = new SelectRemoteWidget('roomBooking.locationsAndRooms.listWithGuids', {}, callback, null, null, null, false);
            var addRoomButton = Html.input("button", {style:{marginRight: pixels(5)}}, $T('Add Room') );
            addRoomButton.observeClick(function(){
                var selectedValue = roomChooser.select.get();
                self.newProcess(selectedValue, function(result){
                    if (result) {
                        var roomName = $('>option:selected', roomChooser.select.dom).text();
                        self.roomList.set(selectedValue, roomName);
                    }
                });
            });
        }

        return Widget.block([Html.div(this.roomDivStyle,this.roomList.draw()), chooserDiv]);
    }
},
    /*
     * @param {String} roomDivStyle A CSS class for the div that will sourround the room list.
     * @param {String} roomListStyle A CSS class for the room list. It will be passed to the inner roomListWidget.
     * @param {list} initialRooms A list of  room that will appear initially.
     * @param {Boolean} allowNew If True, a 'Add Room' button will be present.
     * @param {Function} newProcess A function that will be called when a new room is added to the list.
     * @param {Function} removeProcess A function that will be called when a room is removed.
     */
    function(roomDivStyle, roomListStyle, initialRooms, allowNew, newProcess, removeProcess) {

        var self = this;
        this.roomList = new RoomListWidget(roomListStyle, function(roomToRemove, setResult) {
            return removeProcess(roomToRemove, function(result) {
                setResult(result);
                if(result) {
                    self.roomList.set(roomToRemove, null);
                }
            });
        }, true);
        this.roomDivStyle = any(roomDivStyle, "UIPeopleListDiv");

        if (exists(initialRooms)) {
            each (initialRooms,function(room, guid){
                self.roomList.set(guid, room);
            });
        }

        this.allowNew = any(allowNew, false);
        this.newProcess = any(newProcess, roomListNothing);

     }
);
