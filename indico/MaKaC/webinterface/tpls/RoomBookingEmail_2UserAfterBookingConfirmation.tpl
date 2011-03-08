 Dear ${ firstName },


Your booking has been ACCEPTED.
This is the final confirmation.

INFO:
The conference room ${ reservation.room.getFullName() }
has been booked for ${ reservation.bookedForName }
from ${ formatDate(reservation.startDT.date()) } to ${ formatDate(reservation.endDT.date()) } between ${ reservation.startDT.strftime("%H:%M") } and ${ reservation.endDT.strftime("%H:%M") }

HOW TO GET A KEY (if necessary):
Telephone: ${ reservation.room.whereIsKey }

Booking details:
${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }

BTW, you can always check your bookings here:
${ urlHandlers.UHRoomBookingBookingList.getURL( onlyMy = True ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
