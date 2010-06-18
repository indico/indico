Dear User,


Your booking has been REJECTED by the person responsible for a room.

Room: <%= reservation.room.getFullName() %>
For:  <%= reservation.bookedForName %>
<% if date: %>
Date: <%= date %> ( ONLY THIS DAY IS REJECTED)
<% end %>
<% if not date: %>
Dates: <%= formatDate(reservation.startDT.date()) %> -- <%= formatDate(reservation.endDT.date()) %>
<% end %>
Hours: <%= reservation.startDT.strftime("%H:%M") %> -- <%= reservation.endDT.strftime("%H:%M") %>

Rejection reason:
<%= reason %>


BTW, you can always check your bookings here:
<%= urlHandlers.UHRoomBookingBookingList.getURL( onlyMy = True ) %>
<% includeTpl( 'RoomBookingEmail_Footer' ) %>
