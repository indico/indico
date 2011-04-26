<%page args="room=None, dayDT=None, bars=None, DAY_WIDTH_PX=None, START_H=None"/>
<tr>
    <!-- Date Column -->
    <td>
        <% dateclass = "weekday" %>
        % if dayDT.weekday() in (5, 6):
            <% dateclass = "weekend" %>
        % endif
 <!-- of if block -->
        % if room.isNonBookableDay(dayDT):
            <span title="This room cannot be booked for this date due to maintenance reasons" class="unavailable">
                ${ formatDate(dayDT) }
            </span>
        % else:
            <a href="${ urlHandlers.UHRoomBookingBookingForm.getURL( room )}&day=${ dayDT.day }&month=${ dayDT.month }&year=${ dayDT.year }&ignoreSession=1" class="dateLink ${ dateclass }">
                <span>
                    ${ formatDate(dayDT) }
                </span>
            </a>
        % endif
    </td>

    <!-- Bars Column -->
    <td>
        <div id="dayDiv_${ dayDT }" class="dayDiv">

            <!-- Render each bar... -->
            % for bar in bars:
                <%include file="RoomBookingRoomCalendarBar.tpl" args="bar = bar, DAY_WIDTH_PX = DAY_WIDTH_PX, START_H = START_H, dayDT = dayDT "/>
            % endfor

            <!-- Render each even hour ( 8, 10, 12, 14 o'clock... ) -->
            % for h in xrange( START_H, 25, 2 ):
                <div id="${ "barDivH_" + str( dayDT ) + "_" + str( h ) }" class="calHour" style="left: ${ int( 1.0 * (h-START_H) / 24 * DAY_WIDTH_PX ) }px">${ "%.2d" % h }</div>
            % endfor

        </div>
    </td>
</tr>
