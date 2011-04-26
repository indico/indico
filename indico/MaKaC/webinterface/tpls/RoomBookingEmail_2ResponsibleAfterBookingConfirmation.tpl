Dear User,


Booking of the room '${ reservation.room.getFullName() }' has been CONFIRMED by the room responsible.

You can check booking details here:
${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
