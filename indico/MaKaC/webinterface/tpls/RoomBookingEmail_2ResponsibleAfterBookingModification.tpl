Dear ${ reservation.room.getResponsible().getFirstName() },


Booking of your room has been MODIFIED.

You can check booking details here:
${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
