Dear Assistance Service,


This booking for ${ reservation.room.getFullName() } was modified.

% if reservation.needsAssistance:
User requested ASSISTANCE for room setup.

% endif
% if not reservation.needsAssistance:
User DIDN'T request ASSISTANCE for room setup.
% endif


For:  ${ reservation.bookedForName }
Reason: ${ reservation.reason }
Dates: ${ formatDate(reservation.startDT.date()) } -- ${ formatDate(reservation.endDT.date()) }
Hours: ${ reservation.startDT.strftime("%H:%M") } -- ${ reservation.endDT.strftime("%H:%M") }

You can check details here:
${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
