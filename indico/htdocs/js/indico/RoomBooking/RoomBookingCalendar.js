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

/**
 * Constants
 */
// Calendar starting hour
var START_H = 6;
// Width of the calendar
var DAY_WIDTH_PX = 35 * 12 * 2;
// Room types, used for selecting proper CSS classes
var barClasses = ['barBlocked', 'barPreB', 'barPreConc', 'barUnaval', 'barCand', 'barPreC', 'barConf', 'barOutOfRange'];

var calendarLegend = Html.div({style:{clear: 'both', padding: pixels(5), marginBottom: pixels(10), border: "1px solid #eaeaea", borderRadius: pixels(2)}},
        Html.div( {className:'barLegend', style:{color: 'black'}}, $T('Legend:')),
        Html.div( {className:'barLegend barCand'}, $T('Available')),
        Html.div( {className:'barLegend barConf'}, $T('Conflict')),
        Html.div( {className:'barLegend barUnaval'}, $T('Booked')),
        Html.div( {className:'barLegend barPreB', style:{color: 'black'}}, $T('PRE-Booking')),
        Html.div( {className:'barLegend barPreC', style:{color: 'white'}}, $T('Conflict with PRE-Booking')),
        Html.div( {className:'barLegend barPreConc', style:{color: 'white'}}, $T('Concurrent PRE-Bookings')),
        Html.div( {className:'barLegend barBlocked'}, $T('Blocked')),
        Html.div( {className:'barLegend barOutOfRange'}, $T('Too early to book')));


function compare_alphanum(elem1, elem2) {
    var i_elem1 = parseInt(elem1),
        i_elem2 = parseInt(elem2);

    elem1 = isNaN(i_elem1) ? (elem1 || '').toLowerCase() : i_elem1;
    elem2 = isNaN(i_elem2) ? (elem2 || '').toLowerCase() : i_elem2;

    return elem1 == elem2 ? 0 : (elem1 < elem2 ? -1 : 1);
}


/**
 * Represents a single room in the roombooking
 * @param {object} roomData fossilized room data
 * @param {date} date date of the booking
 */
type ("RoomBookingRoom", [],
        {
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
        function(roomData, date) {
            this.id = roomData.id;
            this.number = roomData.number;
            this.floor = roomData.floor;
            this.building = roomData.building;
            this.location_name = roomData.location_name;
            this.name = roomData.name;
            this.type = roomData.kind;
            this.max_advance_days = roomData.max_advance_days;
            this.details_url = roomData.details_url;
            this.bookingUrl = build_url(roomData.booking_url, {
                start_date: date
            });
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
            this.startDT = IndicoUtil.parseJsonDate(barInfo.startDT);
            this.endDT = IndicoUtil.parseJsonDate(barInfo.endDT);
            // TODO missing canReject and rejectURL
            this.canReject = barInfo.canReject;
            this.rejectURL = barInfo.rejectURL;
            this.blocking = barInfo.blocking_data;
            if (barInfo.forReservation) {
                this.reason = barInfo.forReservation.reason;
                this.owner = barInfo.forReservation.bookedForName;
                this.url = barInfo.forReservation.bookingUrl;
                this.inDB = barInfo.forReservation.id !== null;
            } else if (barInfo.type == 0 && barInfo.blocking_data.type == 'blocking') {
                this.url = barInfo.blocking_data.blocking_url;
                this.inDB = true
            } else if (barInfo.type == 0 && barInfo.blocking_data.type == 'nonbookable') {
                this.inDB = false
            } else {
                this.inDB = false;
            }
            this.type = barClasses[parseInt(barInfo.type)];
            this.resvStartDT = barInfo.resvStartDT && IndicoUtil.parseJsonDate(barInfo.resvStartDT);
            this.resvEndDT = barInfo.resvEndDT && IndicoUtil.parseJsonDate(barInfo.resvEndDT);
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
        function(roomInfo, date, empty) {
            var self = this;
            this.bars = [];
            this.date = date;
            if(!empty) {
                this.room = new RoomBookingRoom(roomInfo.room, date);
                each(roomInfo.bars,
                    function(bar) {
                        self.bars.push(new RoomBookingCalendarBar(bar, self.room));
                });
            } else {
                this.room = new RoomBookingRoom(roomInfo.room, date);
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
        function(options) {
            $.extend(this, options);
            this.days = [];

            for (var date in this.bars) {
                this.days.push(new RoomBookingCalendarDay(this.bars[date], date));
            }
            this.days.sort(function(day1, day2) {
                return IndicoUtil.compare(day1.date, day2.date);
            });
            if (this.finishDate == 'true' && this.days.length) {
                this.endD = this.days[this.days.length-1].date;
                this.startD = this.days[0].date;
            }
            delete this.bars;
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
                    if (showCandidateTip) {
                        resvInfo = $T("Click to book it") + '<br>' + bar.startDT.print("%H:%M") + "  -  " + bar.endDT.print("%H:%M");
                    }
                    else {
                        resvInfo = $T('This bar indicates the time which will be booked.');
                    }
                } else if (bar.type == "barBlocked") {
                    resvInfo = (bar.blocking.type == 'nonbookable') ? [] : [
                        $T("Room blocked by"),
                        ':<br/>',
                        bar.blocking.creator,
                        '<br/>'
                    ];
                    resvInfo = [].concat.apply([], [resvInfo, [$T('Reason'), ': ', bar.blocking.reason]]);
                } else if (bar.type == 'barOutOfRange') {
                    resvInfo = $T('Booking not allowed for this period.<br>This room can only be booked {0} days in advance.').format(bar.room.max_advance_days)
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
                    $(barDiv.dom).on('click', function() {
                        if (self.data.openDetailsInNewTab) {
                            window.open(bar.url);
                        }
                        else {
                            location.href = bar.url;
                        }
                    });
                }
                else if (bar.type == 'barCand' && showCandidateTip) {
                    $(barDiv.dom).click(function(){
                        self._ajaxClick(bar, $(this));
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
             */
            _ajaxClick: function(bar, element) {
                // get conflicts per occurrence
                var conflicts = $('.barDefaultHover').closest('.dayCalendarDiv').map(function() {
                    return $(this).find('.barConf').length;
                }).get();

                var blocked = _.any($('.barDefaultHover').closest('.dayCalendarDiv').map(function() {
                    return $(this).find('.barBlocked').length;
                }).get());

                var outOfRange = _.any($('.barDefaultHover').closest('.dayCalendarDiv').map(function() {
                    return $(this).find('.barOutOfRange').length;
                }).get());

                if (outOfRange) {
                    this._setDialog("search-again");
                    $('#booking-dialog-content').html($T("This room cannot booked more than {0} days in advance.").format(bar.room.max_advance_days));
                    $('#booking-dialog').dialog("open");
                    return;
                }

                var any_conflict = _.any(conflicts);
                var all_conflicts = conflicts.length && _.every(conflicts, function(e) { return !!e; });

                if (all_conflicts && !blocked) {
                    this._setDialog("search-again");
                    $('#booking-dialog-content').html($T("This room cannot be booked due to conflicts with existing reservations or room blockings."));
                    $('#booking-dialog').dialog("open");
                } else if (any_conflict && !blocked) {
                    this._setDialog("skip-conflict", bar);
                    $('#booking-dialog-content').html($T("This booking contains conflicts with existing reservations or blockings."));
                    $('#booking-dialog').dialog("open");
                } else {
                    if (bar.room.type != "privateRoom" && !blocked) {
                        this._proceedToBooking(bar);
                    } else {
                        this._handleProtected(element, bar.room.id, bar.blocking && bar.blocking.id, bar);
                    }
                }
            },

            _handleProtected: function(element, room_id, blocking_id, bar) {
                var self = this;

                indicoRequest("roomBooking.room.bookingPermission", {
                    room_id: room_id,
                    blocking_id: blocking_id,
                    start_dt: bar.resvStartDT.print('%H:%M %Y-%m-%d'),
                    end_dt: bar.resvEndDT.print('%H:%M %Y-%m-%d')
                }, function(result, error) {
                    if (!error && !exists(result.error)) {
                        if (!result.can_book) {
                            self._setDialog("search-again");
                            element.addClass("barProt");
                            if (result.is_reservable && result.group) {
                                var protection = '<strong>' + result.group + '</strong>';
                                $('#booking-dialog-content').html(format($T("Bookings of this room are limited to members of {0}."), [protection]));
                            } else {
                                $('#booking-dialog-content').html($T("You are not authorized to book this room."));
                            }
                            $('#booking-dialog').dialog("open");
                        }

                        else if (result.blocked) {
                            var flexibility = '.' + element.data('flexibility');
                            $('.barDefault.barCand' + flexibility).addClass('barConf');
                            self._setDialog("search-again");
                            $('#booking-dialog-content').html(
                                (result.blocking_type === 'blocking')
                                    ? $T("This room is blocked on this date and you don't have permissions to book it.")
                                    : $T("This room is not available on this date.")
                            );
                            $('#booking-dialog').dialog("open");
                        }

                        else {
                            self._proceedToBooking(bar);
                        }
                    } else {
                        IndicoUtil.errorReport(error || result.error);
                    }
                });
            },

            _proceedToBooking: function(bar) {
                $('#start_dt').val(Util.formatDateTime(bar.resvStartDT));
                $('#end_dt').val(Util.formatDateTime(bar.resvEndDT));
                $('#room_id').val(bar.room.id);
                $('#periodForm').submit();
            },

            _setDialog: function(type, bar) {
                var self = this;

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
                                    // Reload current page via GET (i.e. back to step 1); remove anchor if there's one
                                    location.href = location.href.replace(/#.*$/, '');
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
                                    self._proceedToBooking(bar);
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
                return Html.div({}, this.drawHeader(), this.drawContent());
            }
        },
        /**
         * Object used to draw roombooking calendar out of reservation data.
         * @params {RoomBookingCalendarData} data reservations data
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

                var roomHasBars = _.some(roomInfo.bars, function(bar) {
                    return bar.type != 'barBlocked';
                });
                var container = $('<div class="room-row">')
                    .data('protected', roomInfo.room.type)
                    .toggleClass('room-row-empty', !roomHasBars).append(
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
                        var roomHasBars = _.some(room.bars, function(bar) {
                            return bar.type != 'barBlocked';
                        });
                        rooms.push(roomDiv);
                        if(roomHasBars) {
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
                    var highlight = !self.data.repeatFrequency
                                    || (index == self.data.flexibleDays
                                    || (index - self.data.flexibleDays) % (2 * self.data.flexibleDays + 1) == 0);
                    days.push(self.drawDay(day, highlight));
                });

                return this.data.days.length != 0 ? Html.div({},days) : Html.div({style:{width:pixels(700), margin: '2em auto'}, className: 'infoMessage'}, $T('No results found in the given period of time.'));
            }
        },
        /**
         * Object used to draw roombooking calendar out of reservation data.
         * @params {RoomBookingCalendarData} data reservations data
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

                    var link = Html.a({
                        href: build_url(Indico.Urls.RoomBookingBookRoom, {
                            start_date: day.date,
                            roomLocation: this.room.location_name,
                            roomID: this.room.id
                        }),
                        className: 'dateLink ' + dateClass
                    }, Util.formatDateTime(day.date, IndicoDateTimeFormats.DefaultHourless, "%Y-%m-%d"));

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
                                adjust: {mouse: true, x: 11, y: 13}
                            }
                        });
                    }
                    return new XElement(container.get(0));
                }
            },

            drawHeader: function(){
                if (this.room)
                    var detailsUrl = build_url(this.room.details_url, {preview_months: 3});
                    var singleDayHeader = Html.div({
                        className:"bookingTitle",
                        style:{marginBottom: pixels(20), marginTop: pixels(18), padding: 0}
                    }, Html.a({href:detailsUrl, style:{paddingLeft: pixels(5), fontSize:"x-small"}}, $T("( show 3 months preview )" )));
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

            COMPARE_FUNCTIONS: {
                room: function (elem1, elem2){
                    if (elem1.room.building != elem2.room.building) {
                        return compare_alphanum(elem1.room.building, elem2.room.building);
                    } else if (elem1.room.floor != elem2.room.floor) {
                        return compare_alphanum(elem1.room.floor, elem2.room.floor);
                    } else if (elem1.room.number != elem2.room.number) {
                        return compare_alphanum(elem1.room.number, elem2.room.number);
                    }

                    return 0;
                },
                date: function(elem1, elem2){
                    return compare_alphanum(elem1.startDT.print("%y%m%d"), elem2.startDT.print("%y%m%d"));
                },
                time: function(elem1, elem2){
                    return compare_alphanum(elem1.startDT.print("%H%M"), elem2.startDT.print("%H%M"));
                },
                owner: function(elem1, elem2) {
                    return compare_alphanum(elem1.owner, elem2.owner);
                },
                reason: function(elem1, elem2) {
                    return compare_alphanum(elem1.reason, elem2.reason);
                },
            },

            drawBars: function(sortBy) {
                var self = this;

                sortBy = sortBy || 'room';

                this.bars.sort(function (elem1, elem2) {
                    return self.ascendingSort * self.COMPARE_FUNCTIONS[sortBy](elem1, elem2);
                });

                this.sortedBy = sortBy;
                return _.map(this.bars, this.drawReservation.bind(this));
            },

            /**
             * Draws a single reservation
             * @param {RoomBookingCalendarBar} bar reservation to be drawn
             */
            drawReservation: function(bar){
                // Conflict, prebooking conflict and concurrent prebooking bars don't represent bookings.
                // They're added to the calendar to highlight some events.
                if(!(bar.type == 'barPreC' || bar.type == 'barConf' || bar.type == 'barPreConc' || bar.type == 'barCand')) {
                    var showBookingLink = Html.a({href:bar.url}, $T("Show"));
                    var rejectionLink;
                    // XXX is this still used?
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
                        attrs.onclick = "window.open(" + JSON.stringify(bar.url) + ");";
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

                var self = this,
                    sort_links = {},
                    header = $('<div class="booking-list-header">');

                function draw_sort_link(criterion, caption) {
                    return $('<a href="#"/ class="sort-link sort-link-' + criterion + '">').append(
                        caption,
                        $('<img class="arrow arrow-up"/>').attr('src', imageSrc('upArrow')).hide(),
                        $('<img class="arrow arrow-down"/>').attr('src', imageSrc('downArrow')).hide()
                    ).click(function() {
                        var $this = $(this);

                        self.ascendingSort = self.sortedBy == criterion ? -self.ascendingSort : 1;

                        // toggle arrow
                        header.find('.arrow').hide();
                        $this.find(self.ascendingSort == 1 ? '.arrow-up' : '.arrow-down').show();

                        self.barsDiv.set(self.drawBars(criterion));

                        return false;
                    });
                }

                this.ascendingSort = 1;

                [['room', $T('Room')],
                   ['reason', $T('Reason')],
                   ['owner', $T('Booked for')],
                   ['date', $T('Date')],
                   ['time', $T('Time')]].forEach(function(el) {
                       sort_links[el[0]] = draw_sort_link(el[0], el[1]);
                   });

                sort_links.room.find('.arrow-up').show();

                header.append(sort_links.room,
                              $('<span class="sort-link sort-link-reason-for"/>').append(
                                  sort_links.reason, ' / ', sort_links.owner),
                              sort_links.date,
                              sort_links.time);

                this.barsDiv = Html.div({}, this.drawBars("room"));

                return Html.div({}, new Html(header.get(0)), this.barsDiv);

            },

            /**
             * Main drawing method. Draws a summary if there are any reservations.
             */
            draw: function(){
                if( _.size(this.bars) > 0 ){
                    var self = this;
                    var contentLoaded = false;
                    var showContent = false;
                    var arrowDown = Html.img({src:imageSrc("menu_arrow_black"), style:{display:"inline"}});
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
                    // XXX I'm pretty sure this it no used anymore
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
        function(data){
            this.data = data;
            this.rejectAllLink = data.rejectAllLink;
            this.bars = this.data.getBars();
        });

/**
 * A bar used to change calendar date. It supports going to next and previous period
 * and choosing a specified date from a calendar as well.
 */
type ("RoomBookingNavBar", [],
        {

            /**
             * Main drawing method
             */
            draw: function(firstHeader){
                var self = this;
                var startD = moment(self.data.firstDay, ['YYYY-MM-DD', 'DD/MM/YYYY']);
                var endD = moment(self.data.lastDay, ['YYYY-MM-DD', 'DD/MM/YYYY']);
                var periodDays = endD.diff(startD, 'days') + 1; // number of days
                var periodTitle = periodDays == 1 ? $T('day') :
                                  periodDays == 7 ? $T('week') : $T('period');
                var format = 'dddd, DD MMMM YYYY';
                var verbosePeriod = (self.data.firstDay == self.data.lastDay)
                    ? endD.format(format)
                    : '{0} ➟ {1}'.format(startD.format(format), endD.format(format));

                function loadNewPeriod(start, end) {
                    var form = $('#room-booking-calendar-form');
                    form.find('input[name="start_date"]').val(moment(start).format(self.data.paramFormat));
                    form.find('input[name="end_date"]').val(moment(end).format(self.data.paramFormat));
                    form.submit();
                }

                function showDateSelector() {
                    var dlg = new DateRangeSelector(startD.toDate(), endD.toDate(), loadNewPeriod,
                                                    $T("Choose Period"), true);
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
                    'title': self.data.canNavigate ? $T('Change period') : undefined,
                    'class': 'i-button icon-calendar ' + (self.data.canNavigate ? 'arrow' : ''),
                    'html': verbosePeriod,
                    'css': {
                        'fontWeight': 'normal',
                        'cursor': self.data.canNavigate ? 'pointer': 'default',
                        'pointerEvents': self.data.canNavigate ? 'auto': 'none'
                    },
                    'click': function(e) {
                        e.preventDefault();
                        if(self.data.canNavigate) {
                            showDateSelector();
                        }
                    }
                });
                var prevButton = $('<a>', {
                    'href': '#',
                    'title': $T('Previous') + ' ' + periodTitle,
                    'class': 'i-button icon-only icon-prev',
                    'click': function(e) {
                        e.preventDefault();
                        loadNewPeriod(startD.subtract(periodDays, 'days'), endD.subtract(periodDays, 'days'));
                    }
                });
                var nextButton = $('<a>', {
                    'href': '#',
                    'title': $T('Next') + ' ' + periodTitle,
                    'class': 'i-button icon-only icon-next',
                    'click': function(e) {
                        e.preventDefault();
                        loadNewPeriod(startD.add(periodDays, 'days'), endD.add(periodDays, 'days'));
                    }
                });
                var filterButton = $('<a>', {
                    'href': '#',
                    'title': 'Filters',
                    'class': 'i-button icon-only arrow icon-filter',
                    'data-toggle': 'dropdown'
                });
                var filterDropdown = $('<ul class="dropdown">');
                $('<li>', {
                    'class': 'toggle',
                    'text': $T('Hide empty rooms/days'),
                    'data': {
                        'state': $.jStorage.get(keyHideEmpty, true)
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
                var toolbarGroup = $('<div>', {'class': 'group left'}).appendTo(toolbar);
                if (!self.data.canNavigate) {
                    toolbarGroup.append(calendarButton);
                }
                else {
                    toolbarGroup.append(prevButton);
                    toolbarGroup.append(calendarButton);
                    toolbarGroup.append(nextButton);
                    if (firstHeader) {
                        toolbarGroup = $('<div>', {'class': 'group right'}).appendTo(toolbar);
                        toolbarGroup.append(filterButton);
                        toolbarGroup.append(filterDropdown);
                        toolbar.dropdown();
                    }
                }

                return Html.div({}, toolbarContainer[0]);
            }
        },
        function(data){
            this.data = data;
        });

/**
 * Widget drawing room booking calendar and its summary.
 */
type ("RoomBookingCalendar", [],
        {
            draw: function() {
                var parts = [];

                if (this.data.showLegend) {
                    parts.push(calendarLegend);
                }

                if (this.data.showNavBar) {
                    parts.push(new RoomBookingNavBar(this.data).draw(true));
                }

                parts.push(this.roomBookingCalendarContent.draw());

                if (this.data.showNavBar) {
                    parts.push(new RoomBookingNavBar(this.data).draw(false));
                }

                if (this.data.showSummary) {
                    parts.push(this.roomBookingCalendarSummary.draw());
                }

                return parts;
            },

            addRepeatabilityBarsHovers: function(){
                // Repeat daily booking hover support
                var flexibleNumber = this.data.repeatFrequency ? (2 * this.data.flexibleDays + 1) : 0;
                $('.wholeDayCalendarDiv').each(function(indexDiv) {
                    var flexibleIndex = flexibleNumber ? indexDiv % flexibleNumber : indexDiv;
                    $(this).find('.barCand').each(function(indexCand) {
                        var flexibility = 'repetition-{0}-{1}'.format(indexCand, flexibleIndex);
                        $(this).addClass(flexibility).data('flexibility', flexibility);
                    });
                });

                $('.barCand, .barBlocked').each(function() {
                    var $this = $(this);
                    var candBar = $this.hasClass('barCand') ? $this : $this.prev('.barCand');
                    var flexibility = candBar.data('flexibility');
                    $(this).mouseover(function() {
                        $('.wholeDayCalendarDiv').find('.barCand.' + flexibility).addClass('barDefaultHover');
                    }).mouseleave(function() {
                        $('.barCand').removeClass('barDefaultHover');
                    });
                });
            }
        },

        function(options) {
            options = $.extend({}, {
                bars: null, // list of bars
                dayAttrs: null, // day attributes
                firstDay: null, // first day (for period selector)
                lastDay: null, // last day (for period selector)
                specificRoom: false,
                repeatFrequency: '0',
                finishDate: null,
                flexibleDays: 0,
                rejectAllLink: '',
                openDetailsInNewTab: false, // open reservation details when clicking a bar in a new tab
                showLegend: true,
                showSummary: true, // "display booking summary" link on the bottom
                showNavBar: true, // the "< date >" navbar and the filter button
                canNavigate: true, // if disabled the navbar only shows the current date range but does not allow changes
                paramFormat: 'DD/MM/YYYY'
            }, options);

            this.data = new RoomBookingCalendarData(options);

            if (!this.data.specificRoom) {
                this.roomBookingCalendarContent = new RoomBookingManyRoomsCalendarDrawer(this.data);
            }
            else {
                this.roomBookingCalendarContent = new RoomBookingSingleRoomCalendarDrawer(this.data);
            }
            this.roomBookingCalendarSummary = new RoomBookingCalendarSummaryDrawer(this.data);
        }
);
