Dear User,


Your booking has been REJECTED by the person responsible for a room.

Room: ${ reservation.room.getFullName() }
For:  ${ reservation.bookedForName }
% if date:
Date: ${ date } ( ONLY THIS DAY IS REJECTED)
% endif
% if not date:
Dates: ${ formatDate(reservation.startDT.date()) } -- ${ formatDate(reservation.endDT.date()) }
% endif
Hours: ${ reservation.startDT.strftime("%H:%M") } -- ${ reservation.endDT.strftime("%H:%M") }

Rejection reason:
${ reason }

Booking details:
${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }


BTW, you can always check your bookings here:
${ urlHandlers.UHRoomBookingBookingList.getURL( onlyMy = True ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
