Dear User,


A booking has been REJECTED by the person responsible for the room "${ reservation.room.getFullName() }".

Booking:
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


You can check booking details here:
TODO: urlHandlers.UHRoomBookingBookingDetails.getURL(reservation)
<%include file="RoomBookingEmail_Footer.tpl"/>
