<% exclDays="" %>
% if isinstance(reservation.getExcludedDays(),list) and len(reservation.getExcludedDays()) > 0:
    <% exclDays=" (Note that there are %s excluded days. For further info, check your reservation)"%len(reservation.getExcludedDays()) %>
% endif

Dear ${ firstName },


The conference room ${ reservation.room.getFullName() }
has been booked for ${ reservation.bookedForName }
reason: ${ reservation.reason }
from ${ formatDate(reservation.startDT.date()) } to ${ formatDate(reservation.endDT.date()) } between ${ reservation.startDT.strftime("%H:%M") } and ${ reservation.endDT.strftime("%H:%M") } ${ exclDays }
Access: ${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }

If you find that you will not be using this room, please cancel this booking by going to this URL and clicking "Cancel Booking":

${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }

so that the room can be booked by somebody else.

NOTE: please be aware that in special (rare) cases the person
responsible for this room may reject your booking. In that case,
you will be instantly notified by e-mail.

% if reservation.usesAVC:
You have booked a room equipped with remote collaboration features and indicated that you intend to use them. After your meeting, you will be able to give IT service managers feedback about your video/phone conference by accessing this URL:
https://espace.cern.ch/AVC-workspace/videoconference/Lists/User%20Satisfaction%20in%20CERN%20Videoconference%20Rooms/NewForm.aspx
Thanks in advance for your feedback

% endif
HOW TO GET A KEY (if necessary):
Telephone: ${ reservation.room.whereIsKey }

If you are the creator of the bookings, you can check them here:
${ urlHandlers.UHRoomBookingBookingList.getURL( onlyMy = True ) }
<%include file="RoomBookingEmail_Footer.tpl"/>
