
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
		<% if bars.has_key(day.date()): %>
        	<% includeTpl( 'RoomBookingManyRoomsCalendarDay', dayD = day.date(), roomBarsList = bars[day.date()], DAY_WIDTH_PX = DAY_WIDTH_PX, START_H = START_H ) %>
		<% end %>
    <% end %>

</div>
