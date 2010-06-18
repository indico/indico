Dear <%= firstName %>,


<% if date: %>
You have REMOVED one date from your booking:
<% end %>
<% else: %>
You have CANCELLED your booking:
<% end %>

<%= urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) %>
Room: <%= reservation.room.getFullName() %>
For:  <%= reservation.bookedForName %>
Reason: <%= reservation.reason %>
Dates:
<% if date: %>
<%= formatDate(date) %>
<% end %>
<% else: %>
<%= formatDate(reservation.startDT.date()) %> -- <%= formatDate(reservation.endDT.date()) %>
<% end %>
Hours: <%= reservation.startDT.strftime("%H:%M") %> -- <%= reservation.endDT.strftime("%H:%M") %>


BTW, you can always check your bookings here:
<%= urlHandlers.UHRoomBookingBookingList.getURL( onlyMy = True ) %>
<% includeTpl( 'RoomBookingEmail_Footer' ) %>
