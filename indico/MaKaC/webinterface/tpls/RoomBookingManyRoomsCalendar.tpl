
<!-- Room Calendar ================================================================== -->

<!-- Constant: pixels width of a single day -->
<% DAY_WIDTH_PX = 30 * 12 * 2  %> <!-- OK for 800x600 display -->
<% START_H = 6                 %> <!-- Assume day starts at START_H o'clock -->

<div id="calendarContainer">

    <!-- LEGEND for schedule -->
    &nbsp;Key:<div class="barUnaval" style="display: inline; position:relative; font-size: 80%; margin-left: 8px; padding: 0px 5px 0px 5px;"> <%= _("Booking")%></div>
    <div class="barPreB" style="display: inline; position:relative; font-size: 80%; margin-left: 8px; padding: 0px 5px 0px 5px;"> <%= _("PRE-Booking")%></div>
    <div class="barCand" style="display: inline; position:relative; font-size: 80%; margin-left: 8px; padding: 0px 5px 0px 5px;"> <%= _("New Booking")%></div>
    <div class="barConf" style="display: inline; position:relative; font-size: 80%; margin-left: 8px; color: White; padding: 0px 5px 0px 5px;"> <%= _("Conflict")%></div>
    <div class="barPreC" style="display: inline; position:relative; font-size: 80%; margin-left: 8px; padding: 0px 5px 0px 5px;"> <%= _("Conflict with PRE-Booking")%> </div>
    <div class="barPreConc" style="display: inline; position:relative; font-size: 80%; margin-left: 8px; padding: 0px 5px 0px 5px;"> <%= _("Concurrent&nbsp;PRE-Bookings")%></div>
    <br />
    <br />

    <!-- Render each day -->
    <% for day in iterdays( calendarStartDT, calendarEndDT ): %>
        <% dayD = day.date() %>
		<% if bars.has_key(day.date()): %>
        	<div id="calendarDayContainer">
            <table>

                <tr style="height: 40px;">
                    <td width="120px">
                        <% if dayD: %>
                            <strong><%= formatDate(dayD) %></strong>
                        <% end %>
                        <% if not dayD: %>
                             <%= _("Date")%>
                        <% end %>
                    </td>
                    <td style="width: <%= DAY_WIDTH_PX %>px; ">
                        <div style="height: 12px; position: relative;">
                            <% for h in xrange( START_H, 25, 2 ): %>
                                <div id="barDivH_Hours" style="position: absolute; height: 10px; left: <%= int( 1.0 * (h-START_H) / 24 * DAY_WIDTH_PX ) %>px; font-size: 10px; " >
                                    <%= "%.2d" % h %><span style="font-size: 8px">:00</span>
                                </div>
                            <% end %>
                        </div>
                    </td>
                </tr>

                <!-- Render each room -->
                <% for roomBars in bars[dayD]: %>
                    <% room = roomBars.room %>
                    <tr>
                        <!-- Room Column -->
                        <td width="120px">
                            <a href="<%= urlHandlers.UHRoomBookingBookingForm.getURL( room )%>&day=<%= dayD.day %>&month=<%= dayD.month %>&year=<%= dayD.year %>" class="roomLink <%= roomClass( room ) %>">
                                <span class="<%= roomClass( room ) %>" >
                                    <%= room.building %>-<%= room.floor %>-<%= room.roomNr %>
                                    <% if room.name != str(room.building) + '-' + str(room.floor) + '-' + str(room.roomNr): %>
                                        <br><small>(<%= room.name %>)</small>
                                    <% end %>
                                </span>
                            </a>
                        </td>

                        <!-- Bars Column -->
                        <td>
                            <div class="dayDiv"> <!-- id="roomDiv_<= room.guid >" -->

                                <!-- Render each bar... -->
                                <% for bar in roomBars.bars: %>
                                    <% r = bar.forReservation %>
                                    <% left = int( 1.0 * ( (bar.startDT.hour-START_H) * 60 + bar.startDT.minute ) / (24*60) * DAY_WIDTH_PX  ) %>
                                    <% diff = ( bar.endDT.hour - bar.startDT.hour ) * 60 + ( bar.endDT.minute - bar.startDT.minute ) %>
                                    <% width = int( 1.0 * diff / (24*60) * DAY_WIDTH_PX ) - 1 %>
                                    <% id = "barDiv_" + str(room.id) + "_" + str( dayD ) + "_" + str( bar.startDT.time() ) %>
                                    <% resvInfo = "%s  -  %s<br />%s<br />%s" % (verbose_t( bar.startDT.time() ), verbose_t( bar.endDT.time() ), escapeAttrVal( r.bookedForName ), escapeAttrVal( r.reason ) ) %>
                                    <% resvUrl = bookingDetailsUH.getURL( r ) %>

                                    <%
                                    if bar.type == Bar.UNAVAILABLE:
                                        barClass = 'barUnaval'
                                    %>
                                    <% end %>

                                    <%
                                    if bar.type == Bar.CANDIDATE:
                                        barClass = 'barCand'
                                        resvUrl = "#conflicts"
                                    %>
                                    <% end %>

                                    <%
                                    if bar.type == Bar.CONFLICT:
                                        barClass = 'barConf'
                                    %>
                                    <% end %>

                                    <%
                                    if bar.type == Bar.PREBOOKED:
                                        barClass = 'barPreB'
                                    %>
                                    <% end %>

                                    <%
                                    if bar.type == Bar.PRECONFLICT:
                                        barClass = 'barPreC'
                                    %>
                                    <% end %>

                                    <%
                                    if bar.type == Bar.PRECONCURRENT:
                                        barClass = 'barPreConc'
                                    %>
                                    <% end %>

                                    <div id="<%= id %>" class="<%= barClass %>" style="cursor: pointer; width: <%= width %>px; left: <%= left %>px;" onmouseover="domTT_activate(this, event, 'content', '<%= resvInfo %>', 'delay', 100, 'maxWidth', 320, 'styleClass', 'tip' );" onclick="window.location = '<%=resvUrl%>';"></div>

                                <% end %>

                                <!-- Render each even hour ( 8, 10, 12, 14 o'clock... ) -->
                                <% for h in xrange( START_H, 25, 2 ): %>
                                    <div id="<%= "barDivH_" + str(room.id) + "_" + formatDate(dayD) + "_" + str( h ) %>" class="calHour" style="left: <%= int( 1.0 * (h-START_H) / 24 * DAY_WIDTH_PX ) %>px"><%= "%.2d" % h %></div>
                                <% end %>

                            </div>
                        </td>
                    </tr>

                <% end %>

            </table>
            </div>
		<% end %>
    <% end %>

</div>
