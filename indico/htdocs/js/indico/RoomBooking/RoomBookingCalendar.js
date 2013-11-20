/* This file is part of Indico.
 * Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

/**
 * Constants
 */
// Calendar starting hour
var START_H = 6;
// Width of the calendar
var DAY_WIDTH_PX = 35 * 12 * 2;
// Room types, used for selecting proper CSS classes
var barClasses = ['barBlocked', 'barPreB', 'barPreC', 'barUnaval', 'barCand', 'barPreConc', 'barConf'];


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

var calendarLegend = Html.div({style:{cssFloat: 'left', clear: 'both', padding: pixels(5), marginBottom: pixels(10), border: "1px solid #eaeaea", textAlign: "center", borderRadius: pixels(10)}},
        Html.div( {className:'barLegend', style:{color: 'black'}}, $T('Legend:')),
        Html.div( {className:'barLegend barCand'}, $T('Available')),
        Html.div( {className:'barLegend barConf'}, $T('Conflict')),
        Html.div( {className:'barLegend barUnaval'}, $T('Booked')),
        Html.div( {className:'barLegend barPreB', style:{color: 'black'}}, $T('PRE-Booking')),
        Html.div( {className:'barLegend barPreC', style:{color: 'white'}}, $T('Conflict with PRE-Booking')),
        Html.div( {className:'barLegend barPreConc', style:{color: 'white'}}, $T('Concurrent PRE-Bookings')),
        Html.div( {className:'barLegend barBlocked'}, $T('Blocked')));

/**
 * Represents a single room in the roombooking
 * @param {object} roomData fossilized room data
 * @param {date} date date of the booking
 */
type ("RoomBookingRoom", [],
        {
            /**
             * Return booking form url for the specified dates.
             */
            getBookingFormUrl: function(date, repeatability, flexibleDatesRange, minutes, finishDate, startD, endD, ignoreSession){
                var ignSession = any(ignoreSession, false);
                var urlParams = {
                    roomLocation: this.location,
                    roomID: this.id,
                    ignoreSession: 1,
                    repeatability: repeatability
                };
                if (ignSession) {
                    urlParams.ignoreSession = 1;
                }
                else {
                    urlParams.infoBookingMode = 'True';
                }

                if (minutes) {
                    urlParams.hour = date.substr(11, 2);
                    urlParams.minute = date.substr(14, 2);
                    urlParams.hourEnd = date.substr(16, 2);
                    urlParams.minuteEnd = date.substr(19, 2);
                }
                if (typeof repeatability != 'undefined' && repeatability != 'None' && flexibleDatesRange > 0) {
                    var repeatabilityDays;
                    if (repeatability === 0)
                        repeatabilityDays = 1;
                    else if (repeatability < 4)
                        repeatabilityDays = 7 * repeatability;
                    else
                        repeatabilityDays = 35;
                    var roomStartDate = new Date(date.substr(0,4), date.substr(5,2) - 1, date.substr(8,2));
                    var calendarStartDate = new Date(startD.substr(0,4), startD.substr(5,2) - 1, startD.substr(8,2));
                    while (roomStartDate >= calendarStartDate)
                        roomStartDate.setDate(roomStartDate.getDate() - repeatabilityDays);
                    roomStartDate.setDate(roomStartDate.getDate() + repeatabilityDays);
                    urlParams.year = roomStartDate.getFullYear();
                    urlParams.month = roomStartDate.getMonth() + 1;
                    urlParams.day = roomStartDate.getDate();
                    urlParams.yearEnd = endD.substr(0, 4);
                    urlParams.monthEnd = endD.substr(5, 2);
                    urlParams.dayEnd = endD.substr(8, 2);
                }
                else if (finishDate == 'true') {
                    urlParams.year = startD.substr(0,4);
                    urlParams.month = startD.substr(5,2);
                    urlParams.day = startD.substr(8,2);
                    urlParams.yearEnd = endD.substr(0, 4);
                    urlParams.monthEnd = endD.substr(5, 2);
                    urlParams.dayEnd = endD.substr(8, 2);
                }
                else {
                    urlParams.year = date.substr(0,4);
                    urlParams.month = date.substr(5,2);
                    urlParams.day = date.substr(8,2);
                }
                return build_url(Indico.Urls.RoomBookingForm, urlParams);
            },
            /**
             * Returns room details url.
             */
            getDetailsUrl: function(){
                return build_url(Indico.Urls.RoomBookingDetails, {
                    roomLocation: this.location,
                    roomID: this.id,
                    calendarMonths: 'True'
                });
            },
            /**
             * Gets full name of the room ( building-floor-roomNumber and roomName), wrapped in Div.
             * @param {bool} breakLine if true there will be a breakline between room number and room name
             */
            getFullName: function(){
                var fullName = this.building + "-" + this.floor + "-" + this.number;
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
                var fullName = this.building + "-" + this.floor + "-" + this.number;
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
            this.bookingUrl = build_url(roomData['bookingUrl'], {
                day: date.substring(8,10),
                month: date.substring(5,7),
                year: date.substring(0,4),
                ignoreSession: 1
            });
            this.id = roomData["id"];
            this.location = roomData["locationName"];
        });

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
            this.blocking = barInfo["blocking"];
            this.type = barClasses[parseInt(barInfo["type"])];
        }
        );

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
        );

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
        );

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
        function(reservationBars, dayAttrs, repeatability, finishDate, flexibleDatesRange, dayLimit, overload){
            this.days = [];
            this.dayAttrs = dayAttrs;
            this.repeatability = repeatability;
            this.finishDate = finishDate;
            this.flexibleDatesRange = flexibleDatesRange;
            this.dayLimit = dayLimit;
            this.overload = overload;

            for (var date in reservationBars){
                this.days.push(new RoomBookingCalendarDay(reservationBars[date], date));
            }
            this.days.sort(function(day1, day2){
                return IndicoUtil.compare(day1.date, day2.date);
            });
            if (finishDate == 'true' && this.days.length){
                this.endD = this.days[this.days.length-1].date;
                this.startD = this.days[0].date;
            }
        }
        );

type ("RoomBookingCalendarDrawer", [],
        {
            /**
             * Draws a single reservation
             * @param {RoomBookingCalendarBar} bar reservation to be drawn
             */
            drawBar: function(bar, showCandidateTip){
                var self = this;
                var startHour = bar.startDT.getHours()-START_H;
                var left = ( startHour<0?0:startHour * 60 + bar.startDT.getMinutes() ) / (24*60) * DAY_WIDTH_PX;
                var diff = ( bar.endDT.getHours() - bar.startDT.getHours() + (startHour<0?startHour:0) ) * 60 + ( bar.endDT.getMinutes() - bar.startDT.getMinutes() );
                var width = diff / (24*60) * DAY_WIDTH_PX - 1;
                var resvInfo;

                // TODO: This shouldn't happen! See ticket #942
                if (width < 0) {
                    return Html.div({});
                }

                if (bar.type == "barCand") {
                    resvInfo = "Click to book it <br/>" +
                                  bar.startDT.print("%H:%M") + "  -  " + bar.endDT.print("%H:%M");
                } else if (bar.type == "barBlocked") {
                    resvInfo = $T("Room blocked by") + ":<br/>" +
                                  bar.blocking["creator"] + "<br/>" +
                                  $T('Reason') + ': ' + bar.blocking["message"];
                } else {
                    resvInfo = bar.startDT.print("%H:%M") + "  -  " +
                               bar.endDT.print("%H:%M") + "<br />" +
                               bar.owner + "<br />" +
                               bar.reason;
                }

                var barDiv =  Html.div({
                    className: bar.type + " barDefault",
                    style: {
                        cursor: (bar.inDB || (bar.type == 'barCand' && showCandidateTip) ? 'pointer' : ''),
                        width: pixels(parseInt(width)),
                        left: pixels(parseInt(left))
                    }
                });

                if(bar.inDB) {
                    barDiv.observeClick(function(){
                        window.location = bar.bookingUrl;
                    });
                }

                if (bar.type == 'barCand' && showCandidateTip) {
                    $(barDiv.dom).click(function(){
                        var url = bar.room.getBookingFormUrl(bar.startDT.print("%Y/%m/%d %H:%M") + bar.endDT.print("%H:%M"), self.data.repeatability, self.data.flexibleDatesRange, true, self.data.finishDate, self.data.startD, self.data.endD);
                        self._ajaxClick(bar, url, $(this));
                    });
                }

                $(barDiv.dom).qtip({
                    content: {
                        text: resvInfo
                    },
                    style: {
                        classes: "bold"
                    },
                    position: {
                        target: 'mouse',
                        adjust: { mouse: true, x: 11, y: 13 }
                    },
                    events: {
                        show: function(event, api) {
                            if ((navigator.platform.indexOf("iPad") != -1) || (navigator.platform.indexOf("iPhone") != -1)) {
                                event.preventDefault();
                            }
                        }
                    }
                });

                return barDiv;
            },

            /**
             * Checks if the bar corresponds to a protected room. In that case, checks if the user has permission to book it.
             * @param  {RoomBookingCalendarBar} bar  The bar containing the information of the room.
             * @param  {Integer} user User ID.
             * @return {Boolean}      True if the booking is protected, false otherwise.
             */
            _ajaxClick: function(bar, url, element) {
                // get conflicts per occurrence
                var conflicts = $('.barDefaultHover').closest('.dayCalendarDiv').map(function() {
                    return $(this).find('.barConf').length;
                });

                var blocked = $('.barDefaultHover').closest('.dayCalendarDiv').map(function() {
                    return _.any($(this).find('.barBlocked').length);
                });

                var any_conflict = _.any(conflicts);
                var all_conflicts = conflicts.length && _.every(conflicts, function(e) { return !!e; });

                if (all_conflicts && !blocked) {
                    this._setDialog("search-again");
                    $('#booking-dialog-content').html($T("This room cannot be booked due to conflicts with existing reservations or room blockings."));
                    $('#booking-dialog').dialog("open");
                } else if (any_conflict && !blocked) {
                    this._setDialog("skip-conflict", url);
                    $('#booking-dialog-content').html($T("This booking contains conflicts with existing reservations or blockings."));
                    $('#booking-dialog').dialog("open");
                } else {
                    if (bar.room.type != "privateRoom" && !blocked) {
                        window.location = url;
                    } else {
                        this._handleProtected(element, bar.room.id, bar.blocking.id, url);
                    }
                }
            },

            _handleProtected: function(element, room_id, blocking_id, url) {
                var self = this;

                indicoRequest("roomBooking.room.bookingPermission", {
                    room_id: room_id,
                    blocking_id: blocking_id
                }, function(result, error) {
                    if (!error && !exists(result.error)) {
                        if (!result.can_book) {
                            self._setDialog("search-again");
                            element.addClass("barProt");
                            if (result.group) {
                                var protection = '<strong>' + result.group + '</strong>';
                                $('#booking-dialog-content').html(format($T("Bookings of this room are limited to members of {0}."), [protection]));
                            } else {
                                $('#booking-dialog-content').html($T("You are not authorized to book this room"));
                            }
                            $('#booking-dialog').dialog("open");
                        }

                        else if (result.blocked) {
                            element.addClass("barConf");
                            self._setDialog("search-again");
                            $('#booking-dialog-content').html(
                                $T("This room is blocked on this date and you don't have permissions to book it.")
                            );
                            $('#booking-dialog').dialog("open");
                        }

                        else {
                            window.location = url;
                        }
                    } else {
                        IndicoUtil.errorReport(error || result.error);
                    }
                });
            },

            _setDialog: function(type, url) {
                $('#booking-dialog').dialog({
                    modal: true,
                    resizable: false,
                    autoOpen: false,
                    show: "fade",
                    title: $T("Unable to book")
                });

                switch(type) {
                    case "search-again":
                        $('#booking-dialog').dialog({
                            buttons: {
                                "Search again": function() {
                                    window.location = build_url(Indico.Urls.RoomBookingBookRoom);
                                },
                                Close: function() {
                                    $(this).dialog('close');
                                }
                            }
                        });
                    break;
                    case "skip-conflict":
                        $('#booking-dialog').dialog({
                            buttons: {
                                "Skip conflicting days": function() {
                                    window.location = build_url(url, {skipConflicting: 'on'});
                                },
                                Close: function() {
                                    $(this).dialog('close');
                                }
                            }
                        });
                    break;
                    default:
                        $('#booking-dialog').dialog({
                            buttons: {
                                Close: function() {
                                    $(this).dialog('close');
                                }
                            }
                        });
                }
            },

            /**
             * Draws a row containing hours for a room
             */
            drawSmallHours: function(){
                var hours = $('<div/>');
                for(var i = START_H; i < 25; i += 2 ){
                    var left = (i - START_H) / 24 * DAY_WIDTH_PX;
                    hours.append($('<div class="calHour" />').css('left', left).text(i));
                }
                return hours.children();
            },
            /**
             * Draws a calendar header
             */
            drawHeader: function(){

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
                return Html.div('dayCalendarDivHeader', hours);
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
                switch( this.data.overload ){
                    //Too long period was chosen
                    case 1:
                        return Html.div({}, this.drawHeader(), Html.div({style:{width:pixels(700), margin: '0 auto'}, className: 'errorMessage'}, Html.strong({}, "Error: "), $T("Time span is too large. Please issue a "), Html.a({href:build_url(Indico.Urls.RoomBookingBookRoom)}, $T("more specific query.")), $T("Time span limit is {0} days.").format(this.data.dayLimit)));
                    //Too many results fetched
                    case 2:
                        return Html.div({}, this.drawHeader(), Html.div({style:{width:pixels(700), margin: '0 auto'}, className: 'errorMessage'}, Html.strong({}, "Error: "), $T("Too many possible periods found. Please issue a "), Html.a({href:build_url(Indico.Urls.RoomBookingBookRoom)}, $T("more specific query."))));
                }
                return Html.div({}, this.drawHeader(),  this.drawContent());
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
        function(data){
            this.data = data;
        });

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
                var day_content = $('<div class="dayCalendarDiv">').append($('<div class="time-bar"/>'));

                $.each(roomInfo.bars,
                        function(i, bar){
                            day_content.append(self.drawBar(bar, true).dom);
                        });

                var container = $('<div class="room-row">')
                    .data('protected', roomInfo.room.type)
                    .toggleClass('room-row-empty', !roomInfo.bars.length).append(
                        $('<div class="link">').append(roomLink.dom),
                        day_content);

                return new XElement(container.get(0));

            },

            /**
             * Draws a day cell and all its rooms and reservations
             * @param {RoomBookingCalendarDay} day day to be drawn
             */
            drawDay: function(day, highlight){
                var self = this;
                var rooms = [];
                var hasNonEmpty = false;
                each(day.rooms, function (room) {
                    var roomDiv = self.drawRoom(room);
                    if (roomDiv) {
                        rooms.push(roomDiv);
                        if(room.bars.length) {
                            hasNonEmpty = true;
                        }
                    }
                });

                if(_.size(rooms) > 0) {
                    return Html.div({className:"wholeDayCalendarDiv " + (hasNonEmpty ? '' : 'day-empty'), style: (highlight ? {border: '2px solid #D9EDF7'} : {})},
                                Html.div({className: (highlight ? 'wholeDayCalendarDayHighlight' : ''), style: {width: pixels(800), height: pixels(20), borderBottom: "1px solid #eaeaea", clear: "both"}},
                                        Html.div({style:{cssFloat:'left', fontWeight: 'bold'}}, $.datepicker.formatDate('DD, d MM yy', $.datepicker.parseDate('yy-mm-dd', day.date)))), this.drawHours(), rooms);
                }
            },

            /**
             * Main drawing method. Draws reservations for all stored rooms and days
             */
            drawContent: function(){
                var self = this;
                var days = [];
                $.each(this.data.days, function(index, day){
                    var highlight = self.data.repeatability == '0' || (index == self.data.flexibleDatesRange || (index - self.data.flexibleDatesRange) % (2 * self.data.flexibleDatesRange + 1) == 0);
                    days.push(self.drawDay(day, highlight));
                });

                return this.data.days.length != 0 ? Html.div({},days) : Html.div({style:{width:pixels(700), margin: '2em auto'}, className: 'infoMessage'}, $T('No results found in the given period of time. Please change period.'));
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
        function(data){
            this.RoomBookingCalendarDrawer(data);
        });

type ("RoomBookingSingleRoomCalendarDrawer", ["RoomBookingCalendarDrawer"],
        {
            drawDay: function(day){
                var self = this;
                var day_content = $('<div class="dayCalendarDiv">').append($('<div class="time-bar"/>'));

                $.each(day.rooms[0].bars,
                    function(i, bar){
                        day_content.append(self.drawBar(bar, false).dom);
                });

                var dateClass = "weekday";
                var dateArray = day.date.split('-');
                var date = new Date(dateArray[0], dateArray[1]-1, dateArray[2]);
                if (date.getDay() == 0 || date.getDay() == 6) {
                    dateClass = "weekend";
                }
                if (this.room.nonBookableDates) {
                    return Html.span({title: $T("This room cannot be booked for this date"), className: "unavailable"}, Util.formatDateTime(day.date, IndicoDateTimeFormats.DefaultHourless, "%Y-%m-%d"));
                } else {
                    if(this.data.getDayClass(day)) {
                        dateClass = this.data.getDayClass(day);
                    }
                    var tt = this.data.getDayTooltip(day);
                    if(tt) {
                        tt = tt.replace(/\n/g, '<br>');
                    }
                    var link = Html.a({href:this.room.getBookingFormUrl(day.date, this.data.repeatability, this.data.flexibleDatesRange, false, false, null, null, true),  className : 'dateLink ' + dateClass},
                                      Util.formatDateTime(day.date, IndicoDateTimeFormats.DefaultHourless, "%Y-%m-%d"));

                    var container = $('<div class="room-row">').append(
                        $('<div class="link">').append(link.dom),
                        day_content);

                    if(tt) {
                        $(link.dom).qtip({
                            content: {
                                text: tt
                            },
                            position: {
                                target: 'mouse',
                                adjust: { mouse: true, x: 11, y: 13 }
                            }
                        });
                    }
                    return new XElement(container.get(0));
                }
            },

            drawHeader: function(){
                if( this.room )
                    var singleDayHeader = Html.div({className:"bookingTitle", style:{marginBottom: pixels(20), marginTop: pixels(18)}}, Html.span({className:"groupTitle bookingTitle", style:{borderBottom: pixels(0), paddingTop: pixels(0)}},
                                          $T("Availability for "), this.data.days[0].rooms[0].room.getFullName(false)), Html.a({href:this.room.getDetailsUrl(), style:{paddingLeft: pixels(5), fontSize:"x-small"}}, $T("( show 3 months preview )" )));
                return Html.div({}, singleDayHeader, calendarLegend, this.RoomBookingCalendarDrawer.prototype.drawHeader.call(this));
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
                if (days.length != 0)
                    return Html.div({style:{clear:'both', width:pixels(840), marginTop:pixels(15), marginBottom:pixels(40)}},
                       Html.div({style:{width:pixels(120), height:pixels(20)}},
                                Html.div({style:{cssFloat:'left', fontWeight:'bold'}},
                                    $T("Date")),
                                    this.drawHours()),
                                    days);
                return "";
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
        function(data){
            this.RoomBookingCalendarDrawer(data);
            this.room = this.data.days.length > 0?this.data.days[0].rooms[0].room:null;
        });

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
                            barsDiv.push(self.drawReservation(bar));
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
                if(!(bar.type == 'barPreC' || bar.type == 'barConf' || bar.type == 'barPreConc')) {
                    var showBookingLink = Html.p({className:"fakeLink"}, $T("Show"));
                    showBookingLink.observeClick(function(){
                        window.open(bar.bookingUrl);
                    });
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
                                        if(value) {
                                            window.location = build_url(bar.rejectURL, {reason: textArea.dom.value});
                                        }
                                    }).open();
                        });
                    }

                    var attrs = {}, cursorStyle = '';
                    if(bar.inDB || bar.type == 'barCand') {
                        attrs.onclick = "window.location='" + bar.bookingUrl + "';";
                        cursorStyle = 'pointer';
                    }
                    return Html.div({ onmouseover : "this.style.backgroundColor='#f0f0f0';", onmouseout : "this.style.backgroundColor='#ffffff';", style:{clear:'both', overflow:'auto', cursor:cursorStyle}},
                                Html.div(attrs,
                                    Html.p({style:{cssFloat:'left', width: pixels(175), height:pixels(40)}},bar.room.getFullNameHtml(true)),
                                    Html.p({style:{cssFloat:'left', width: pixels(350), height:'auto'}},bar.reason, Html.br(), bar.owner ),
                                    Html.p({style:{cssFloat:'left', width: pixels(90), height:pixels(40)}},bar.startDT.print("%d/%m/%Y")),
                                    Html.p({style:{cssFloat:'left', width: pixels(75), height:pixels(40)}},bar.startDT.print("%H:%M"), Html.br(), bar.endDT.print("%H:%M"))),
                                Html.p({style:{cssFloat:'left', width: pixels(40), height:pixels(40)}},showBookingLink, rejectionLink));
                } else {
                    return null;
                }
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
                    var contentLoaded = false;
                    var showContent = false;
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
                    });
                    var content = Html.div({});
                    var rejectAllDiv = null;
                    if (this.rejectAllLink) {
                        rejectAllDiv = Html.div({className:"fakeLink", style:{width:pixels(800), textAlign:"center", paddingBottom:pixels(10)}},
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
                    return Html.div({style:{clear:'both', marginTop: pixels(20)}},rejectAllDiv,
                            Html.div({style:{width:pixels(800), textAlign:'center', paddingTop: pixels(10), paddingBottom: pixels(10)}},toggleSummary, arrowDown), content);
                }
            }
        },
        function(data, rejectAllLink){
            this.data = data;
            this.rejectAllLink = rejectAllLink;
            this.bars = this.data.getBars();
        });

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
            draw: function(firstHeader){
                var self = this;
                var verbosePeriod = (this.startD == this.endD)
                    ? $.datepicker.formatDate('DD, d MM yy', $.datepicker.parseDate('dd/mm/yy', this.endD))
                    : $.datepicker.formatDate('DD, d MM yy', $.datepicker.parseDate('dd/mm/yy', this.startD)) + " -> " + $.datepicker.formatDate('DD, d MM yy', $.datepicker.parseDate('dd/mm/yy', this.endD));

                function showDateSelector() {
                    var dlg = new DateRangeSelector(self.startD, self.endD, function(startDate, endDate) {
                        var urlParams = $.extend({
                            sDay: startDate.getDate(),
                            sMonth: startDate.getMonth() + 1,
                            sYear: startDate.getFullYear(),
                            eDay: endDate.getDate(),
                            eMonth: endDate.getMonth() + 1,
                            eYear: endDate.getFullYear()
                        }, self.params);
                        if (self.search) {
                            urlParams.search = 'on';
                        }
                        location.href = build_url(self.formUrl, urlParams);
                    }, $T("Choose Period"), true);
                    dlg.open();
                }

                // empty row filter
                var keyHideEmpty = 'rb-hide-empty-rows-' + $('body').data('userId');
                function toggleHideEmpty(e, state) {
                    $('.room-row-empty, .day-empty').toggle(!state);
                    $.jStorage.set(keyHideEmpty, state);
                }
                _.defer(function() {
                    // Execute the handler function after we have rendered the rows
                    toggleHideEmpty(undefined, $.jStorage.get(keyHideEmpty, false));
                });

                // toolbar buttons
                var calendarButton = $('<a>', {
                    'href': '#',
                    'title': self.newBooking ? undefined : $T('Change period'),
                    'class': 'i-button icon-calendar ' + (self.newBooking ? '' : 'arrow'),
                    'html': verbosePeriod,
                    'css': {
                        'fontWeight': 'normal'
                    },
                    'click': function(e) {
                        e.preventDefault();
                        if(!self.newBooking) {
                            showDateSelector();
                        }
                    }
                });
                var prevButton = $('<a>', {
                    'href': this.prevURL,
                    'title': $T('Previous') + ' ' + this.periodName,
                    'class': 'i-button icon-only icon-prev'
                });
                var nextButton = $('<a>', {
                    'href': this.nextURL,
                    'title': $T('Next') + ' ' + this.periodName,
                    'class': 'i-button icon-only icon-next'
                });
                var filterButton = $('<a>', {
                    'href': '#',
                    'title': 'Filters',
                    'class': 'i-button icon-only arrow icon-filter',
                    'data': {
                        'toggle': 'dropdown'
                    }
                });
                var filterDropdown = $('<ul class="dropdown">');
                $('<li>', {
                    'class': 'toggle',
                    'text': $T('Hide empty rooms/days'),
                    'data': {
                        'state': $.jStorage.get(keyHideEmpty, false)
                    }
                }).on('menu_toggle', toggleHideEmpty).appendTo(filterDropdown);

                // toolbar
                var toolbarContainer = $('<div>', {
                    'class': 'clearfix',
                    css: {
                        'marginBottom': '15px'
                    }
                });
                var toolbar = $('<div>', {
                    'class': 'toolbar left',
                    'css': {
                        'width': '810px'
                    }
                }).appendTo(toolbarContainer);
                var toolbarGroup = $('<div class="group left">').appendTo(toolbar);
                if(self.newBooking) {
                    toolbarGroup.append(calendarButton);
                }
                else {
                    toolbarGroup.append(prevButton);
                    toolbarGroup.append(calendarButton);
                    toolbarGroup.append(nextButton);
                    if(firstHeader) {
                        toolbarGroup = $('<div class="group right">').appendTo(toolbar);
                        toolbarGroup.append(filterButton);
                        toolbarGroup.append(filterDropdown);
                        toolbar.dropdown();
                    }
                }

                if(firstHeader) {
                    return Html.div({}, calendarLegend, toolbarContainer[0]);
                }
                else {
                    return Html.div({}, toolbarContainer[0]);
                }
            }
        },
        function(prevNextBarArgs, data){
            this.prevURL = prevNextBarArgs.prevURL;
            this.newBooking = prevNextBarArgs.newBooking;
            this.nextURL = prevNextBarArgs.nextURL;
            this.formUrl = prevNextBarArgs.formUrl;
            this.periodName = prevNextBarArgs.periodName;
            this.startD = prevNextBarArgs.startD;
            this.endD = prevNextBarArgs.endD;
            this.params = prevNextBarArgs.params;
            this.search = prevNextBarArgs.search;
            this.data = data;
        });

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
                if (this.data.overload)
                    return [new RoomBookingPrevNext(this.prevNextBarArgs, this.data).draw(true),
                            this.roomBookingCalendarContent.draw()];
                if (this.prevNextBarArgs && this.prevNextBarArgs.newBooking)
                    return [new RoomBookingPrevNext(this.prevNextBarArgs, this.data).draw(true),
                            this.roomBookingCalendarContent.draw(),
                            new RoomBookingPrevNext(this.prevNextBarArgs, this.data).draw(false)];
                else if ( this.prevNextBarArgs )
                    return [new RoomBookingPrevNext(this.prevNextBarArgs, this.data).draw(true),
                            this.roomBookingCalendarContent.draw(),
                            new RoomBookingPrevNext(this.prevNextBarArgs, this.data).draw(false),
                            this.roomBookingCalendarSummary.draw()];
                else
                    return [this.roomBookingCalendarContent.draw(),
                            this.roomBookingCalendarSummary.draw()];
            },

            addRepeatabilityBarsHovers: function(){
                // Repeat daily booking hover support
                var flexibleNumber = 2 * this.data.flexibleDatesRange + 1;
                if(this.data.repeatability == '0')
                    flexibleNumber = 0;
                $('.wholeDayCalendarDiv').each(function(indexDiv) {
                    var flexibleIndex = indexDiv % flexibleNumber;
                    $(this).find('.barCand').each(function(indexCand) {
                        $(this).attr('id', indexCand + '-' + flexibleIndex);
                    });
                });

                $('.barCand, .barBlocked').each(function() {
                    var id = $(this).hasClass("barCand")? $(this).attr("id") : $(this).prev(".barCand").attr("id");
                    $(this).mouseover(function() {
                        $('.wholeDayCalendarDiv').find(".barCand#" + id).each(function() {
                            $(this).addClass("barDefaultHover");
                        });
                    }).mouseleave(function() {
                        $('.barCand').removeClass("barDefaultHover");
                    });
                });
            }
        },

        function(reservationBars, dayAttrs, dayLimit, overload, prevNextBarArgs, manyRooms, repeatability, finishDate, flexibleDatesRange, rejectAllLink){
           this.data = new RoomBookingCalendarData(reservationBars, dayAttrs, repeatability, finishDate, flexibleDatesRange, dayLimit, overload);
           this.prevNextBarArgs = prevNextBarArgs;
           if(manyRooms || (prevNextBarArgs && prevNextBarArgs.newBooking)) {
               this.roomBookingCalendarContent = new RoomBookingManyRoomsCalendarDrawer(this.data);
           }
           else {
               this.roomBookingCalendarContent = new RoomBookingSingleRoomCalendarDrawer(this.data);
           }
           this.roomBookingCalendarSummary = new RoomBookingCalendarSummaryDrawer(this.data, rejectAllLink);
        }
);
