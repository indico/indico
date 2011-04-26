Dear ${ firstName },


% if date:
You have REMOVED one date from your booking:
% else:
You have CANCELLED your booking:
% endif

${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }
Room: ${ reservation.room.getFullName() }
For:  ${ reservation.bookedForName }
Reason: ${ reservation.reason }
Dates:
% if date:
${ formatDate(date) }
% else:
${ formatDate(reservation.startDT.date()) } -- ${ formatDate(reservation.endDT.date()) }
% endif
Hours: ${ reservation.startDT.strftime("%H:%M") } -- ${ reservation.endDT.strftime("%H:%M") }

Booking details:
${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }


BTW, you can always check your bookings here:
${ urlHandlers.UHRoomBookingBookingList.getURL( onlyMy = True ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
