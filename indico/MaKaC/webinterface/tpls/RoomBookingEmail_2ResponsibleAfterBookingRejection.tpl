Dear User,


A booking has been REJECTED by the person responsible for the room "${ reservation.room.getFullName() }".

Booking:
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


You can check booking details here:
${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
