/**
 * Constants
 */
// Calendar starting hour
var START_H = 6;
// Width of the calendar
var DAY_WIDTH_PX = 35 * 12 * 2;
// Room types, used for selecting proper CSS classes
var barClasses = ['barPreB', 'barPreC', 'barUnaval', 'barCand',  'barPreConc', 'barConf'];


// Compares two rooms. Mainly used for sorting.
function compareRooms(elem1, elem2){
    if (elem1.room.building != elem2.room.building)
        return IndicoUtil.compare(elem1.room.building, elem2.room.building);
    if (elem1.room.floor != elem2.room.floor)
        return IndicoUtil.compare(elem1.room.floor, elem2.room.floor);
    if (elem1.room.number != elem2.room.number)
        return IndicoUtil.compare(elem1.room.number, elem2.room.number);
    return 0;
}

/**
 * Represents a single room in the roombooking
 * @param {object} roomData fossilized room data
 * @param {date} date date of the booking
 */
type ("RoomBookingRoom", [],
        {
            /**
             * Return booking form url for the specified date.
             */
            getBookingFormUrl: function(date){
                return Indico.Urls.RoomBookingForm + "?roomLocation=" + this.location + "&roomID=" + this.id +
                    "&year=" + date.substr(0,4) + "&month=" + date.substr(5,2) + "&day=" + date.substr(8,2) +
                    "&ignoreSession=1";
            },
            /**
             * Returns room details url.
             */
            getDetailsUrl: function(){
                return Indico.Urls.RoomBookingDetails + "?roomLocation=" + this.location + "&roomID=" + this.id +
                    "&calendarMonths=True";
            },
            /**
             * Gets full name of the room ( building-floor-roomNumber and roomName), wrapped in Div.
             * @param {bool} breakLine if true there will be a breakline between room number and room name
             */
            getFullName: function(){
                fullName = this.building + "-" + this.floor + "-" + this.number;
                if( fullName == this.name)
                    return fullName;
                else
                    return fullName + " (" + this.name + ")";
            },
            /**
             * Gets full name of the room ( building-floor-roomNumber and roomName), wrapped in Div.
             * @param {bool} breakLine if true there will be a breakline between room number and room name
             */
            getFullNameHtml: function( breakLine ){
                fullName = this.building + "-" + this.floor + "-" + this.number;
                if( fullName == this.name)
                    return Html.div({},fullName);
                else
                    return Html.div({},fullName, breakLine?Html.br():"", Html.small({}, "(" + this.name + ")"));
            }
        },
        function(roomData, date){
            this.number = roomData["roomNr"];
            this.floor = roomData["floor"];
            this.building = roomData["building"];
            this.name = roomData["name"];
            this.type = roomData["type"];
            this.bookingUrl = roomData["bookingUrl"] + '&day=' + date.substring(8,10) + '&month=' + date.substring(5,7) + '&year=' + date.substring(0,4) + '&ignoreSession=1';
            this.id = roomData["id"];
            this.location = roomData["locationName"];
        })

/**
 * Represents single reservation (bar)
 * @param {object} barInfo fossilized bar data
 * @param {object} room fossilized room data
 */
type ("RoomBookingCalendarBar", [],
        {},
        function(barInfo, room){
            this.room = room;
            this.startDT = IndicoUtil.parseJsonDate(barInfo["startDT"]);
            this.endDT = IndicoUtil.parseJsonDate(barInfo["endDT"]);
            this.canReject = barInfo["canReject"];
            this.rejectURL = barInfo["rejectURL"];
            this.reason = barInfo["forReservation"]["reason"];
            this.owner = barInfo["forReservation"]["bookedForName"];
            this.bookingUrl = barInfo["forReservation"]["bookingUrl"];
            this.inDB = barInfo.forReservation.id !== null;
            this.type = barClasses[parseInt(barInfo["type"])];
        }
        )

/**
 * Represents a single room and all its reservations for a specified day.
 * @param {object} roomInfo fossilized room data
 * @param {date} date date of reservations
 */
type ("RoomBookingCalendarRoom", [],
        {
            /**
             * Gets all bars from the room
             */
            getBars: function(){
                return this.bars;
            }
        },
        function(roomInfo, date, empty){
            var self = this;
            this.bars = [];
            this.date = date;
            if(!empty){
                this.room = new RoomBookingRoom(roomInfo["room"], date);
                each(roomInfo.bars,
                    function(bar){
                        self.bars.push(new RoomBookingCalendarBar(bar, self.room));
                });
            } else {
                this.room = new RoomBookingRoom(roomInfo, date);
            }
        }
        )

/**
 * Represents a single day
 * @param {object} dayInfo contains fossilized day data
 * @param {date} date selected day
 */
type ("RoomBookingCalendarDay", [],
        {
            /**
             * Gets list of all reservations for this day
             */
            getBars: function(){
                var bars = [];
                each(this.rooms,
                    function(room){
                        bars = bars.concat(room.getBars());
                });
                return bars;
            }
        },
        function(dayInfo, date){
            var self = this;
            this.date = date;
            this.rooms = [];
            each(dayInfo, function(room){
                self.rooms.push(new RoomBookingCalendarRoom(room, date));
            });
            this.rooms.sort(compareRooms);
        }
        )

/**
 * Contains data about all reservations made in specified period
 * @param {object} reservationBars fossilized reservations
 */
type ("RoomBookingCalendarData", [],
        {
            /**
             * Gets all reservations
             */
            getBars: function(){
                var bars = [];
                for( var day = 0; day < _.size(this.days); ++day )
                    bars = bars.concat(this.days[day].getBars());
                return bars;
            },
            getDayClass: function(day) {
                if(!this.dayAttrs[day.date]) {
                    return;
                }
                return this.dayAttrs[day.date].className || '';
            },
            getDayTooltip: function(day) {
                if(!this.dayAttrs[day.date]) {
                    return;
                }
                return this.dayAttrs[day.date].tooltip || '';
            }
        },
        function(reservationBars, dayAttrs){
            this.days = [];
            this.dayAttrs = dayAttrs;
            for (var date in reservationBars){
                this.days.push(new RoomBookingCalendarDay(reservationBars[date], date));
            }
            this.days.sort(function(day1, day2){
                return IndicoUtil.compare(day1.date, day2.date);
            });
        }
        )

type ("RoomBookingCalendarDrawer", [],
        {
            /**
             * Draws a single reservation
             * @param {RoomBookingCalendarBar} bar reservation to be drawn
             */
            drawBar: function(bar){
                var startHour = bar.startDT.getHours()-START_H;
                var left = ( startHour<0?0:startHour * 60 + bar.startDT.getMinutes() ) / (24*60) * DAY_WIDTH_PX;
                var diff = ( bar.endDT.getHours() - bar.startDT.getHours() + (startHour<0?startHour:0) ) * 60 + ( bar.endDT.getMinutes() - bar.startDT.getMinutes() );
                var width = diff / (24*60) * DAY_WIDTH_PX - 1;
                if (width < 0) {
                    // TODO: This shouldn't happen! See ticket #942
                    return Html.div({});
                }
                var resvInfo = bar.startDT.print("%H:%M") + "  -  " +
                               bar.endDT.print("%H:%M") + "<br />" + bar.owner +
                               "<br />" + bar.reason;
                var barDiv =  Html.div({
                    className: bar.type,
                    style: {cursor: (bar.inDB ? 'pointer' : ''), width: pixels(parseInt(width)), left: pixels(parseInt(left))}});
                if(bar.inDB) {
                    barDiv.observeClick(function(){
                        window.location = bar.bookingUrl;
                    });
                }
                $(barDiv.dom).qtip({
                    content: {
                        text: resvInfo
                    }
                });
                return barDiv;
            },
            /**
             * Draws a row containing hours for a room
             */
            drawSmallHours: function(){
                var hours = [];
                for(var i = START_H; i < 25; i += 2 ){
                    var left = (i - START_H) / 24 * DAY_WIDTH_PX;
                    hours.push(Html.div({className : "calHour", style:{left:left}},i));
                }
                return hours;
            },
            /**
             * Draws a calendar header
             */
            drawHeader: function(){
                return Html.div({},'Key:',
                        Html.div( {className:"barUnaval", style:{display: 'inline', position:'relative', fontSize: '80%', marginLeft: pixels(8), padding: "0px 5px 0px 5px"}}, $T("Booking")),
                        Html.div( {className:"barPreB", style:{display: 'inline', position:'relative', fontSize: '80%', marginLeft: pixels(8), padding: "0px 5px 0px 5px"}}, $T("PRE-Booking")),
                        Html.div( {className:"barCand", style:{display: 'inline', position:'relative', fontSize: '80%', marginLeft: pixels(8), padding: "0px 5px 0px 5px"}}, $T("New Booking")),
                        Html.div( {className:"barConf", style:{display: 'inline', position:'relative', fontSize: '80%', marginLeft: pixels(8), padding: "0px 5px 0px 5px", color: "white"}}, $T("Conflict")),
                        Html.div( {className:"barPreC", style:{display: 'inline', position:'relative', fontSize: '80%', marginLeft: pixels(8), padding: "0px 5px 0px 5px"}}, $T("Conflict with PRE-Booking")),
                        Html.div( {className:"barPreConc", style:{display: 'inline', position:'relative', fontSize: '80%', marginLeft: pixels(8), padding: "0px 5px 0px 5px"}}, $T("Concurrent PRE-Bookings")));
            },
            /**
             * Draws hours row for a room header
             */
            drawHours: function(){
                var hours = [];
                for(var i = START_H; i < 25; i += 2 ){
                    var left = (i - START_H) / 24 * DAY_WIDTH_PX;
                    hours.push(Html.div({className : 'calHour', style:{'left':left, fontSize:pixels(10)}},i, Html.span({style:{fontSize: pixels(8)}}, ":00")));
                }
                return Html.div({className:'dayCalendarDiv'},hours);
            },
            /**
             * Draws content of the drawer. Need to be overloaded.
             */
            drawContent: function(){
                return "";
            },
            /**
             * Main drawing method.
             */
            draw: function(){
                switch( this.overload ){
                    //Too long period was chosen
                    case 1:
                        var overloadDiv = Html.div({style:{fontSize:pixels(16), textAlign:'center', marginBottom:pixels(12), color:"#881122"}}, $T("Too large time span. Please issue a more specific query."));
                        break;
                    //Too many results fetched
                    case 2:
                        var overloadDiv = Html.div({style:{fontSize:pixels(16), textAlign:'center', marginBottom:pixels(12), color:"#881122"}}, $T("Too many results. Searching period was shortened."));
                        break;
                    //Not overloaded
                    default:
                        var overloadDiv = null;
                }
                return Html.div({style:{clear:'both'}}, overloadDiv, this.drawHeader(), this.drawContent());
            }
        },
        /**
         * Object used to draw roombooking calendar out of reservation data.
         * @params {RoomBookingCalendarData} data reservations data
         * @params {int} overload The type of overload.
         * 0 - no overload,
         * 1 - too long period chosen (no bookings will be displayed) ,
         * 2 - too many bookings fetched. Booking from the shorter period are going to be displayed.
         */
        function(data, overload){
            this.data = data;
            this.overload = overload;
        })

type ("RoomBookingManyRoomsCalendarDrawer", ["RoomBookingCalendarDrawer"],
        {
            /**
             * Draws a room cell and all its reservations
             * @param {RoomBookingCalendarRoom} roomInfo room to be drawn
             */
            drawRoom: function(roomInfo){
                var self = this;
                var roomLink = Html.a({href:roomInfo.room.bookingUrl, className : 'roomLink ' + roomInfo.room.type},
                        roomInfo.room.getFullNameHtml(true));
                var bars = [];
                each(roomInfo.bars,
                        function(bar){
                    bars.push(self.drawBar(bar));
                })
                return Html.div({style:{clear:'both', width:pixels(120), paddingTop:pixels(5)}}, Html.div({style:{cssFloat:'left'}},roomLink), Html.div('dayCalendarDiv',bars, this.drawSmallHours()));
            },

            /**
             * Draws a day cell and all its rooms and reservations
             * @param {RoomBookingCalendarDay} day day to be drawn
             */
            drawDay: function(day){
                var self = this;
                var rooms = [];
                each(day.rooms,
                    function(room){
                        roomDiv = self.drawRoom(room);
                        if(roomDiv)
                            rooms.push(roomDiv);
                })
                if(_.size(rooms) > 0)
                    return Html.div({style:{width:pixels(840), marginTop:pixels(40)}}, Html.div({style:{width:pixels(120), height:pixels(20)}}, Html.div({style:{cssFloat:'left', fontWeight:'bold'}}, Util.formatDateTime(day.date, IndicoDateTimeFormats.DefaultHourless, "%Y-%m-%d")), this.drawHours()), rooms);
            },

            /**
             * Main drawing method. Draws reservations for all stored rooms and days
             */
            drawContent: function(){
                var self = this;
                var days = [];
                each(this.data.days, function(day){
                        days.push(self.drawDay(day));
                });
                return Html.div({},days);
            }
        },
        /**
         * Object used to draw roombooking calendar out of reservation data.
         * @params {RoomBookingCalendarData} data reservations data
         * @params {int} overload The type of overload.
         * 0 - no overload,
         * 1 - too long period chosen (no bookings will be displayed) ,
         * 2 - too many bookings fetched. Booking from the shorter period are going to be displayed.
         */
        function(data, overload){
            this.RoomBookingCalendarDrawer(data, overload);
        })

type ("RoomBookingSingleRoomCalendarDrawer", ["RoomBookingCalendarDrawer"],
        {
            drawDay: function(day){
                var self = this;
                var bars = [];
                each(day.rooms[0].bars,
                        function(bar){
                    bars.push(self.drawBar(bar));
                });


                var dateClass = "weekday";
                var dateArray = day.date.split('-');
                var date = new Date(dateArray[0], dateArray[1]-1, dateArray[2]);
                if (date.getDay() == 0 || date.getDay() == 6)
                    dateClass = "weekend";
                if (this.room.nonBookableDates) {
                    return Html.span({title: $T("This room cannot be booked for this date due to maintenance reasons"), className: "unavailable"}, Util.formatDateTime(day.date, IndicoDateTimeFormats.DefaultHourless, "%Y-%m-%d"));
                } else {
                    if(this.data.getDayClass(day)) {
                        dateClass = this.data.getDayClass(day);
                    }
                    var tt = this.data.getDayTooltip(day);
                    if(tt) {
                        tt = tt.replace(/\n/g, '<br>');
                    }
                    var link = Html.a({href:this.room.getBookingFormUrl(day.date),  className : 'dateLink ' + dateClass},
                                      Util.formatDateTime(day.date, IndicoDateTimeFormats.DefaultHourless, "%Y-%m-%d"));
                    var div = Html.div({style:{clear:'both', paddingTop:pixels(5)}},
                        Html.div({style:{display:'block', cssFloat:'left', width:pixels(125)}}, link),
                        Html.div({style:{cssFloat:'left'}},
                        Html.div('dayCalendarDiv',bars, this.drawSmallHours())));
                    if(tt) {
                        $(link.dom).qtip({
                            content: {
                                text: tt
                            }
                        });
                    }
                    return div;
                }
            },

            drawHeader: function(){
                if( this.room )
                    var singleDayHeader = Html.div({style:{marginBottom: pixels(20)}}, Html.span({className:"formTitle", style:{borderBottom: pixels(0)}},
                                                  $T("Availability for "), this.data.days[0].rooms[0].room.getFullName(false)),
                                                  Html.a({href:this.room.getDetailsUrl(), style:{fontSize:"x-small"}}, $T("  ( show 3 months preview)" )));
                else
                    var singleDayHeader = Html.div({className:"formTitle", style:{borderBottom: pixels(0), margin: pixels(20)}},
                                          $T("No bookings were made "));
                return Html.div({}, singleDayHeader, this.RoomBookingCalendarDrawer.prototype.drawHeader.call(this));
            },
            /**
             * Draws a day cell and all its rooms and reservations
             * @param {RoomBookingCalendarDay} day day to be drawn
             */
            drawContent: function(){
                var self = this;
                var days = [];
                each(this.data.days, function(day){
                    days.push(self.drawDay(day));
                });
                return Html.div({style:{width:pixels(840), marginTop:pixels(40)}},
                       Html.div({style:{width:pixels(120), height:pixels(20)}},
                                Html.div({style:{cssFloat:'left', fontWeight:'bold'}},
                                    $T("Date")),
                                    this.drawHours()),
                                    days);
                }
        },
        /**
         * Object used to draw roombooking calendar out of reservation data.
         * @params {RoomBookingCalendarData} data reservations data
         * @params {int} overload The type of overload.
         * 0 - no overload,
         * 1 - too long period chosen (no bookings will be displayed) ,
         * 2 - too many bookings fetched. Booking from the shorter period are going to be displayed.
         */
        function(data, overload){
            this.RoomBookingCalendarDrawer(data, overload);
            this.room = this.data.days.length > 0?this.data.days[0].rooms[0].room:null;
        })

/**
 * Object used to draw roombooking summary out of reservation data.
 * @params {RoomBookingCalendarData} data reservations data
 */
type ("RoomBookingCalendarSummaryDrawer", [],
        {
            /**
             * Draws reservations list sorted by specified order
             * @param {string} sortBy sorting order
             */
            drawBars: function( sortBy ) {
                var self = this;
                var ascending = this.sortedBy == sortBy?-this.ascendingSort:1;
                var sortFunc;
                var barsDiv = [];
                switch( sortBy ){
                    case "reason":
                        sortFunc = function(elem1, elem2){
                            return ascending * IndicoUtil.compare(elem1.reason, elem2.reason);
                        };
                        break;
                    case "owner":
                        sortFunc = function(elem1, elem2){
                            return ascending * IndicoUtil.compare(elem1.owner, elem2.owner);
                        };
                        break;
                    case "date":
                        sortFunc = function(elem1, elem2){
                            return ascending * IndicoUtil.compare(elem1.startDT.print("%y%m%d"), elem2.startDT.print("%y%m%d"));
                        };
                        break;
                    case "time":
                        sortFunc = function(elem1, elem2){
                            return ascending * IndicoUtil.compare(elem1.startDT.print("%H%M"), elem2.startDT.print("%H%M"));
                        };
                        break;
                    case "name":
                        sortFunc = function(elem1, elem2){
                            return ascending * compareRooms(elem1, elem2);
                        };
                        break;
                }
                if(sortFunc)
                    this.bars.sort(sortFunc);
                each(this.bars,
                        function(bar){
                            barsDiv.push(self.drawReservation(bar))
                });
                this.sortedBy = sortBy;
                this.ascendingSort = ascending;
                return barsDiv;
            },

            /**
             * Draws a single reservation
             * @param {RoomBookingCalendarBar} bar reservation to be drawn
             */
            drawReservation: function(bar){
                // Conflict, prebooking conflict and concurrent prebooking bars don't represent bookings.
                // They're added to the calendar to highlight some events.
                if( !(bar.type == 'barPreC' || bar.type == 'barConf' || bar.type == 'barPreConc') ) {
                    var rejectionLink;
                    if (bar.canReject){
                        rejectionLink = Html.p({className:"fakeLink"},$T("Reject"));
                        rejectionLink.observeClick(function() {
                            var textArea = Html.textarea({rows:4, cols:40});
                            var popup = new ConfirmPopup($T("Rejecting a booking"),
                                    Html.div({style:{textAlign:'center'}},
                                            Html.p({},$T('Are you sure you want to REJECT the booking for ' + bar.startDT.print("%H:%M %d/%m/%Y") + '?')),
                                            Html.p({},$T('If so, please give a reason:')), textArea),
                                    function(value) {
                                        if(value)
                                            window.location = bar.rejectURL + "&reason=" + textArea.dom.value;
                                    }).open();
                        });
                    }

                    var attrs = {}, cursorStyle = '';
                    if(bar.inDB) {
                        attrs.onclick = "window.location='" + bar.bookingUrl + "';";
                        cursorStyle = 'pointer';
                    }
                    return Html.div({ onmouseover : "this.style.backgroundColor='#f0f0f0';", onmouseout : "this.style.backgroundColor='#ffffff';", style:{clear:'both', overflow:'auto', cursor:cursorStyle}},
                                Html.div(attrs,
                                    Html.p({style:{cssFloat:'left', width: pixels(175), height:pixels(40)}},bar.room.getFullNameHtml(true)),
                                    Html.p({style:{cssFloat:'left', width: pixels(350), height:'auto'}},bar.reason, Html.br(), bar.owner ),
                                    Html.p({style:{cssFloat:'left', width: pixels(90), height:pixels(40)}},bar.startDT.print("%d/%m/%Y")),
                                    Html.p({style:{cssFloat:'left', width: pixels(75), height:pixels(40)}},bar.startDT.print("%H:%M"), Html.br(), bar.endDT.print("%H:%M"))),
                                Html.p({style:{cssFloat:'left', width: pixels(40), height:pixels(40)}},rejectionLink));
                } else
                    return null;
            },

            /**
             * Draws the header and the body of the summary
             */
            drawSummary: function(){
                var self = this;
                var arrows = {
                    "name" : [Html.img({src:imageSrc("downArrow.png"), style:{display:"none"}}),
                              Html.img({src:imageSrc("upArrow.png"), style:{display:"inline"}})],
                    "owner" : [Html.img({src:imageSrc("downArrow.png"), style:{display:"none"}}),
                              Html.img({src:imageSrc("upArrow.png"), style:{display:"none"}})],
                    "reason" : [Html.img({src:imageSrc("downArrow.png"), style:{display:"none"}}),
                              Html.img({src:imageSrc("upArrow.png"), style:{display:"none"}})],
                    "date" : [Html.img({src:imageSrc("downArrow.png"), style:{display:"none"}}),
                              Html.img({src:imageSrc("upArrow.png"), style:{display:"none"}})],
                    "time" : [Html.img({src:imageSrc("downArrow.png"), style:{display:"none"}}),
                              Html.img({src:imageSrc("upArrow.png"), style:{display:"none"}})]
                };
                var hideArrows = function(){
                    each(arrows, function(arrowArray){
                        arrowArray[0].dom.style.display = "none";
                        arrowArray[1].dom.style.display = "none";
                    });
                };

                var sortByRoomLink = Html.p({className:"fakeLink", style:{cssFloat:'left', width: pixels(175)}},$T("Room "), arrows["name"]);
                sortByRoomLink.observeClick(function(){
                    self.barsDiv.set(self.drawBars("name"));
                    hideArrows();
                    arrows["name"][self.ascendingSort == 1?1:0].dom.style.display = 'inline';
                });

                var sortByOwnerLink = Html.span({className:"fakeLink"},$T("For whom "), arrows["owner"]);
                sortByOwnerLink.observeClick(function(){
                    self.barsDiv.set(self.drawBars("owner"));
                    hideArrows();
                    arrows["owner"][self.ascendingSort == 1?1:0].dom.style.display = 'inline';
                });

                var sortByReasonLink = Html.span({className:"fakeLink"},$T("Reason "), arrows["reason"]);
                sortByReasonLink.observeClick(function(){
                    self.barsDiv.set(self.drawBars("reason"));
                    hideArrows();
                    arrows["reason"][self.ascendingSort == 1?1:0].dom.style.display = 'inline';
                });

                var sortByDateLink = Html.p({className:"fakeLink", style:{cssFloat:'left', width: pixels(90)}},$T("Date "), arrows["date"]);
                sortByDateLink.observeClick(function(){
                    self.barsDiv.set(self.drawBars("date"));
                    hideArrows();
                    arrows["date"][self.ascendingSort == 1?1:0].dom.style.display = 'inline';
                });

                var sortByHourLink = Html.p({className:"fakeLink", style:{cssFloat:'left', width: pixels(75)}},$T("Hours "), arrows["time"]);
                sortByHourLink.observeClick(function(){
                    self.barsDiv.set(self.drawBars("time"));
                    hideArrows();
                    arrows["time"][self.ascendingSort == 1?1:0].dom.style.display = 'inline';
                });

                var header =  Html.div({ style:{clear:'both', overflow:'auto'}},
                            sortByRoomLink,
                            Html.p({style:{cssFloat:'left', width: pixels(350)}},sortByReasonLink, " / ", sortByOwnerLink),
                            sortByDateLink,
                            sortByHourLink
                    );

                this.barsDiv = Html.div({}, this.drawBars("name"));

                return Html.div({}, header, this.barsDiv);
            },

            /**
             * Main drawing method. Draws a summary if there are any reservations.
             */
            draw: function(){
                if( _.size(this.bars) > 0 ){
                    var self = this;
                    contentLoaded = false;
                    showContent = false;
                    var arrowDown = Html.img({src:imageSrc("menu_arrow_black.png"), style:{display:"inline"}});
                    var toggleSummary = Html.span({className:"fakeLink", style:{paddingRight:pixels(2)}},
                            $T("Display room booking summary "));
                    toggleSummary.observeClick(function(){
                        if(!contentLoaded) {
                            contentLoaded = true;
                            content.set(self.drawSummary());
                        }
                        if(showContent) {
                            showContent = false;
                            content.dom.style.display = "none";
                            toggleSummary.dom.innerHTML = $T("Display room booking summary ");
                            arrowDown.dom.style.display = 'inline';
                        }
                        else {
                            showContent = true;
                            content.dom.style.display = "block";
                            toggleSummary.dom.innerHTML = $T("Hide room booking summary");
                            arrowDown.dom.style.display = 'none';
                        }
                    })
                    content = Html.div({});
                    var rejectAllDiv = null;
                    if (this.rejectAllLink) {
                        rejectAllDiv = Html.div({className:"fakeLink", style:{width:pixels(820), textAlign:"center", paddingBottom:pixels(10)}},
                                $T("Reject ALL Conflicting PRE-Bookings"));
                        rejectAllDiv.observeClick( function(){
                            new ConfirmPopup($T("Reject ALL Conflicting PRE-Bookings"),
                                            Html.div({},$T('Are you sure you want to REJECT ALL conflicting PRE-bookings?')),
                                            function(value) {
                                                if(value)
                                                    window.location = self.rejectAllLink;
                                            }).open();
                        });
                    }
                    return Html.div({style:{clear:'both', marginTop: pixels(45)}},rejectAllDiv,
                            Html.div({style:{background:"#F5F5F5", width:pixels(820), textAlign:'center', padding: pixels(10)}},toggleSummary, arrowDown), content);
                }
            }

        },
        function(data, rejectAllLink){
            this.data = data;
            this.rejectAllLink = rejectAllLink;
            this.bars = this.data.getBars();
        })


/**
 * A bar used to change calendar date. It supports going to next and previous period
 * and choosing a specified date from a calendar as well.
 * @param {string} prevURL url of the previous period
 * @param {string} nextURL url of the next period
 * @param {string} formUrl url of the calendar form
 * @param {string} startD period's start date
 * @param {string} endD period's end date
 * @param {string} periodName period's name i.e day, week etc.
 * @param {dict} params additional room bookign parameters
 */
type("RoomBookingPrevNext", [],
        {

            /**
             * Main drawing method
             */
            draw: function(){
                var self = this;
                var prevLink = Html.a({href:this.prevURL, style:{fontSize:'xx-small', cssFloat: 'left', width:"15%"}}, "< " + $T('previous') + " " + this.periodName);
                var nextLink = Html.a({href:this.nextURL, style:{fontSize:'xx-small', cssFloat: 'right'}}, $T('next') + " " + this.periodName + " >");
                var calendarButton = Html.span("fakeLink", $T("change period"));

                calendarButton.observeClick(function() {
                    var dlg = new DateRangeSelector(self.startD, self.endD, function(startDate, endDate) {

                        var redirectUrl =  self.formUrl + "?" + (self.search ? 'search=on&' : '') + "sDay=" + startDate.getDate() +"&sMonth=" + (startDate.getMonth() + 1) + "&sYear=" + startDate.getFullYear() +
                        "&eDay=" + endDate.getDate() +"&eMonth=" + (endDate.getMonth() + 1) + "&eYear=" + endDate.getFullYear();

                        for (var param in self.params)
                            redirectUrl += "&" + param + "=" + self.params[param];

                        window.location = redirectUrl;

                    }, $T("Choose Period"), true);
                    dlg.open();
                });

                var verbosePeriod = this.startD == this.endD? this.endD : this.startD + " -> " + this.endD;

                return Html.div({style:{height:pixels(33), width:pixels(820), backgroundColor:"#F5F5F5", clear:"both", marginTop:pixels(35), marginBottom:pixels(20)}},
                        prevLink, Html.div({style:{width:"70%", textAlign:"center", cssFloat:"left"}}, verbosePeriod, Html.br(), calendarButton), nextLink);
            }
        },
        function(prevNextBarArgs){
            this.prevURL = prevNextBarArgs.prevURL;
            this.nextURL = prevNextBarArgs.nextURL;
            this.formUrl = prevNextBarArgs.formUrl;
            this.periodName = prevNextBarArgs.periodName;
            this.startD = prevNextBarArgs.startD;
            this.endD = prevNextBarArgs.endD;
            this.params = prevNextBarArgs.params;
            this.search = prevNextBarArgs.search;
        })

/**
 * Widget drawing room booking calendar and its summary.
 * @param {dic} reservationBars fossilized reservations
 * @param {bool} showEmptyRooms indicates if data of all rooms was sent.
 * If false only rooms with bookings were sent.
 * @param {string} prevUrl url of the previous period
 * @param {string} nextUrl url of the next period
 * @param {string} formUrl url of the calendar form
 * @param {string} startD period's start date
 * @param {string} endD period's end date
 * @param {string} periodName period's name i.e day, week etc.
 * @param {dict} params additional room booking parameters
 */
type ("RoomBookingCalendar", [],
        {
            draw: function(){
                if( this.prevNextBarArgs )
                    return [new RoomBookingPrevNext(this.prevNextBarArgs).draw(),
                            this.roomBookingCalendarContent.draw(),
                            new RoomBookingPrevNext(this.prevNextBarArgs).draw(),
                            this.roomBookingCalendarSummary.draw()];
                else
                    return [this.roomBookingCalendarContent.draw(),
                            this.roomBookingCalendarSummary.draw()];
            }
        },
        function(reservationBars, dayAttrs, overload, prevNextBarArgs, manyRooms, rejectAllLink){
            this.data = new RoomBookingCalendarData(reservationBars, dayAttrs);
            this.prevNextBarArgs = prevNextBarArgs;
            if(manyRooms)
                this.roomBookingCalendarContent = new RoomBookingManyRoomsCalendarDrawer(this.data, overload);
            else
                this.roomBookingCalendarContent = new RoomBookingSingleRoomCalendarDrawer(this.data, overload);
            this.roomBookingCalendarSummary = new RoomBookingCalendarSummaryDrawer(this.data, rejectAllLink);
        }
        )
