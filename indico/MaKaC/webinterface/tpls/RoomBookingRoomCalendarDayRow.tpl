<tr>
    <!-- Date Column -->
    <td>
        <% dateclass = "weekday" %>
        <% if dayDT.weekday() in (5, 6): %>
            <% dateclass = "weekend" %>
        <% end %> <!-- of if block -->
        <a href="<%= urlHandlers.UHRoomBookingBookingForm.getURL( room )%>&day=<%= dayDT.day %>&month=<%= dayDT.month %>&year=<%= dayDT.year %>" class="dateLink <%= dateclass %>">
            <span>
                <%= formatDate(dayDT) %>
            </span>
        </a>
    </td>

    <!-- Bars Column -->
    <td>
        <div id="dayDiv_<%= dayDT %>" class="dayDiv">

            <!-- Render each bar... -->
            <% for bar in bars: %>
                <% includeTpl( 'RoomBookingRoomCalendarBar', bar = bar, DAY_WIDTH_PX = DAY_WIDTH_PX, START_H = START_H, dayDT = dayDT ) %>
            <% end %>

            <!-- Render each even hour ( 8, 10, 12, 14 o'clock... ) -->
            <% for h in xrange( START_H, 25, 2 ): %>
                <div id="<%= "barDivH_" + str( dayDT ) + "_" + str( h ) %>" class="calHour" style="left: <%= int( 1.0 * (h-START_H) / 24 * DAY_WIDTH_PX ) %>px"><%= "%.2d" % h %></div>
            <% end %>

        </div>
    </td>
</tr>
