Dear AVC Support,


This booking for ${ reservation.room.getFullName() } was modified.

User is going to use video-conferencing equipment:
    ${ ", ".join(reservation.getUseVC())+ "\n" }

% if reservation.needsAVCSupport:
User requested ASSISTANCE with video-conferencing equipment.

% endif
% if not reservation.needsAVCSupport:
User DIDN'T request assistance with video-conferencing equipment.
% endif


For:  ${ reservation.bookedForName }
Reason: ${ reservation.reason }
Dates: ${ formatDate(reservation.startDT.date()) } -- ${ formatDate(reservation.endDT.date()) }
Hours: ${ reservation.startDT.strftime("%H:%M") } -- ${ reservation.endDT.strftime("%H:%M") }

You can check details here:
${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
