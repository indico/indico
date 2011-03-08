Dear ${ firstName },


TINY ACTION IS REQUIRED TO PROLONG YOUR BOOKING

If you are still interested in the following booking:

${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }
Room: ${ reservation.room.getFullName() }
For:  ${ reservation.bookedForName }
Reason: ${ reservation.reason }
Dates: ${ formatDate(reservation.startDT.date()) } -- ${ formatDate(reservation.endDT.date()) }
Hours: ${ reservation.startDT.strftime("%H:%M") } -- ${ reservation.endDT.strftime("%H:%M") }

please just click this link:
${ prolongationLink }

WARNING: If you will not click the link, your booking may be DELETED.

++++

Explanation: your booking is considered "heavy". You will be asked
every 2 weeks for prolongation. The ONLY action required on your
part is clicking the link. Just to let us know you are still
interested in this booking. Otherwise the booking may be deleted to
let other people book the room. This is to ensure that large, heavy
bookings do not block rooms unnecessarily.

Thank you for your understanding.


BTW, you can always check your bookings here:
${ urlHandlers.UHRoomBookingBookingList.getURL( onlyMy = True ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
