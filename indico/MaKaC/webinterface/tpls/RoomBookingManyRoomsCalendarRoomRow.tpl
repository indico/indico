<%page args="dayD=None, room=None, bars=None, DAY_WIDTH_PX=None, START_H=None, numberOfRooms=None"/>
<tr>
    <!-- Room Column -->
    <td width="120px">
        <a href="${ urlHandlers.UHRoomBookingBookingForm.getURL( room )}&day=${ dayD.day }&month=${ dayD.month }&year=${ dayD.year }&ignoreSession=1" class="roomLink ${ roomClass( room ) }">
            <span class="${ roomClass( room ) }" >
                ${ room.building }-${ room.floor }-${ room.roomNr }
                % if room.name != str(room.building) + '-' + str(room.floor) + '-' + str(room.roomNr):
                    <br><small>(${ room.name })</small>
                % endif
            </span>
        </a>
    </td>

    <!-- Bars Column -->
    <td>
        <div class="dayDiv"> <!-- id="roomDiv_<= room.guid >" -->

            <!-- Render each bar... -->
            % for bar in bars:
                <%include file="RoomBookingRoomCalendarBar.tpl" args="bar = bar, DAY_WIDTH_PX = DAY_WIDTH_PX, START_H = START_H, dayDT = dayD "/>
            % endfor

            <!-- Render each even hour ( 8, 10, 12, 14 o'clock... ) -->
            % for h in xrange( START_H, 25, 2 ):
                <div id="${ "barDivH_" + str(room.id) + "_" + formatDate(dayD) + "_" + str( h ) }" class="calHour" style="left: ${ int( 1.0 * (h-START_H) / 24 * DAY_WIDTH_PX ) }px">${ "%.2d" % h }</div>
            % endfor

        </div>
    </td>
</tr>
