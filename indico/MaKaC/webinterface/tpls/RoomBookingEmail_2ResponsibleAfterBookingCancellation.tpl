Dear ${ reservation.room.getResponsible().getFirstName() },

% if date:
The date ${ formatDate(date) } from a booking that concerns one of your rooms has been CANCELLED by the user.
% else:
Booking of your room has been CANCELLED by the user.
% endif

You can check booking details here:
${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
