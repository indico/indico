
<!--
Day Calendar is composed of room rows ( RoomBookingManyRoomsCalendar*RoomRow* )
Room row is composed of of bars, showing particular reservations
Calendar 1-----* DayRow 1-----* Bar 
-->

<!-- Room Calendar ================================================================== -->

<div id="calendarDayContainer">

<table>

    <!-- Schedule Header: hours -->   
	<% includeTpl( 'RoomBookingCalendarHeader', DAY_WIDTH_PX = DAY_WIDTH_PX, START_H = START_H, dayDT = dayD ) %>

    <!-- Render each room -->
    <% for roomBars in roomBarsList: %>
        <% includeTpl( 'RoomBookingManyRoomsCalendarRoomRow', dayD = dayD, room = roomBars.room, bars = roomBars.bars, DAY_WIDTH_PX = DAY_WIDTH_PX, START_H = START_H, numberOfRooms = len( roomBarsList ) ) %>
    <% end %>

</table>

</div>
