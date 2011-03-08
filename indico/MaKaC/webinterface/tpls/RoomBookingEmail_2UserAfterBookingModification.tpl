Dear ${ firstName },


Your booking has been MODIFIED.

Room: ${ reservation.room.getFullName() }
For:  ${ reservation.bookedForName }
Reason: ${ reservation.reason }
Dates: ${ formatDate(reservation.startDT.date()) } -- ${ formatDate(reservation.endDT.date()) }
Hours: ${ reservation.startDT.strftime("%H:%M") } -- ${ reservation.endDT.strftime("%H:%M") }

You can check details here:
${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }

BTW, you can always check your bookings here:
${ urlHandlers.UHRoomBookingBookingList.getURL( onlyMy = True ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
