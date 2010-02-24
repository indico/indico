<% declareTemplate(newTemplateStyle=True) %>
<!--
Room Calendar is composed of day rows ( RoomBookingRoomCalendar*DayRow* )
Day row is composed of of bars, showing particular reservations ( RoomBookingRoomCalendar*Bar* )
Calendar 1-----* DayRow 1-----* Bar
-->

<!-- Conflicts - Textual ============================================================ -->
<% if withConflicts: %>
    <br /><br />
    <span class="formTitle" style="border-bottom-width: 0px">Conflicts</span><br /><br />
    <p style="margin-left: 10px;">
        <% if thereAreConflicts: %>
            <span style="color: Red; font-weight: bold;"><%= conflictsNumber %>&nbsp;<%= _("conflict(s) with other bookings")%></span><br /><br />
            <% includeTpl( 'RoomBookingConflicts' ) %>
        <% end %>
        <% if not thereAreConflicts: %>
            <span style="color: Green">No conflicts with confirmed bookings, press the "<%= buttonText %>" button to save your booking.</span>
        <% end %>
    </p>
<% end %>


<!-- Room Calendar ================================================================== -->
<br /><br />
<span class="formTitle" style="border-bottom-width: 0px">Availability for <%= room.name %></span>
<% if not withConflicts: %>
    <a href="<%= urlHandlers.UHRoomBookingRoomDetails.getURL( room, calendarMonths = True ) %>"<small>( <%= _("show 3 months preview")%>)</small></a>
<% end %>

<br /><br />

<!-- Constant: pixels width of a single day -->
<% DAY_WIDTH_PX = 30 * 12 * 2  %> <!-- OK for 800x600 display -->
<% START_H = 6                 %> <!-- Assume day starts at START_H o'clock -->

<div id="calendarContainer">

<!-- LEGEND for schedule -->

&nbsp;Key:<div class="barUnaval" style="display: inline; position:relative; font-size: 80%; margin-left: 8px; padding: 0px 5px 0px 5px;"> <%= _("Booking")%></div>
<div class="barPreB" style="display: inline; position:relative; font-size: 80%; margin-left: 8px; padding: 0px 5px 0px 5px;"> <%= _("PRE-Booking")%></div>
<div class="barCand" style="display: inline; position:relative; font-size: 80%; margin-left: 8px; padding: 0px 5px 0px 5px;"> <%= _("New Booking")%></div>
<div class="barConf" style="display: inline; position:relative; font-size: 80%; margin-left: 8px; color: White; padding: 0px 5px 0px 5px;"> <%= _("Conflict")%></div>
<div class="barPreC" style="display: inline; position:relative; font-size: 80%; margin-left: 8px; padding: 0px 5px 0px 5px;"> <%= _("Conflict with PRE-Booking")%></div>
<div class="barPreConc" style="display: inline; position:relative; font-size: 80%; margin-left: 8px; padding: 0px 5px 0px 5px;"> <%= _("Concurrent&nbsp;PRE-Bookings")%></div>
<br />
<br />

<table>

    <!-- Schedule Header: hours -->
    <% includeTpl( 'RoomBookingCalendarHeader', DAY_WIDTH_PX = DAY_WIDTH_PX, START_H = START_H, dayD = None ) %>

    <!-- Render each day -->
    <% for day in iterdays( calendarStartDT, calendarEndDT ): %>
        <% includeTpl( 'RoomBookingRoomCalendarDayRow', dayDT = day.date(), bars = bars[day.date()], DAY_WIDTH_PX = DAY_WIDTH_PX, START_H = START_H ) %>
    <% end %>

</table>
</div>

<!--
This script sets positions of small-hours and bars AFTER the
page load (body onload event). This is probably the only
cross-browser way to position relatively to parent element.
-->
<script type="text/javascript">
        function room_booking_calendar_position()
        {
            // Take all divs from calendarContainer
            cntDiv = document.getElementById( 'calendarContainer' )
            barDivs = cntDiv.getElementsByTagName( "div" )
            for ( j = 0; j < barDivs.length; ++j )
            {
                barDiv = barDivs[j]
                if ( barDiv.id )
                {
                    // Skip not interesting divs
                    if ( barDiv.id.indexOf( 'barDiv' ) == -1 )
                        continue;
                    // Get parent position
                    dayDiv = barDiv.parentNode
                    dayPos = findPos( dayDiv )
                    dayX = dayPos[0]
                    dayY = dayPos[1]
                    // Set div position
                    barDiv.style.left = dayX + parseInt( barDiv.style.left, 10 ) + "px"
                    barDiv.style.top = dayY + "px"
                }
            }
        }
        // add to body onload events
        // add_load_event( room_booking_calendar_position );
</script>
