 Dear AVC Support,


A booking for the room ${ reservation.room.getFullName() } has been CANCELLED.

For:  ${ reservation.bookedForName }
Reason: ${ reservation.reason }
Dates: ${ formatDate(reservation.startDT.date()) } -- ${ formatDate(reservation.endDT.date()) }
Hours: ${ reservation.startDT.strftime("%H:%M") } -- ${ reservation.endDT.strftime("%H:%M") }

 You can check details here:
${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
