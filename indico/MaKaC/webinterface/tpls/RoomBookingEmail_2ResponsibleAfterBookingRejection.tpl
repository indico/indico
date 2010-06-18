Dear User,


A booking has been REJECTED by the person responsible for the room "<%= reservation.room.getFullName() %>".

Booking:
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


You can check booking details here:
<%= urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) %>
<% includeTpl( 'RoomBookingEmail_Footer' ) %>