Dear User,


Your booking has been REJECTED by the person responsible for a room.

Room: ${ reservation.room.getFullName() }
For:  ${ reservation.booked_for_name }
% if date:
Date: ${ date } (ONLY THIS DAY IS REJECTED)
% endif
% if not date:
Dates: ${ formatDate(reservation.start_date.date()) } -- ${ formatDate(reservation.end_date.date()) }
% endif
Hours: ${ reservation.start_date.strftime('%H:%M') } -- ${ reservation.end_date.strftime('%H:%M') }

Rejection reason:
${ reason }

Booking details:
TODO urlHandlers.UHRoomBookingBookingDetails.getURL(reservation)


BTW, you can always check your bookings here:
${ urlHandlers.UHRoomBookingBookingList.getURL(onlyMy=True) }
<%include file="RoomBookingEmail_Footer.tpl"/>
