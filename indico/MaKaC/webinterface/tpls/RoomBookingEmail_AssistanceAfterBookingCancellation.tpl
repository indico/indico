Dear Conference Rooms Service,


${currentUser.getStraightFullName()} has cancelled the following meeting. Support is NOT needed anymore.

For:  ${ reservation.bookedForName }
Reason: ${ reservation.reason }
Room: ${ reservation.room.getFullName() }
Dates: ${ formatDate(reservation.startDT.date()) } -- ${ formatDate(reservation.endDT.date()) }
Hours: ${ reservation.startDT.strftime("%H:%M") } -- ${ reservation.endDT.strftime("%H:%M") }

 You can check details here:
${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
