Dear <%= reservation.room.getResponsible().getFirstName() %>,

<% if date: %>
The date <%= formatDate(date) %> from a booking that concerns one of your rooms has been CANCELLED by the user.
<% end %>
<% else: %>
Booking of your room has been CANCELLED by the user.
<% end %>

You can check booking details here:
<%= urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) %>
<% includeTpl( 'RoomBookingEmail_Footer' ) %>