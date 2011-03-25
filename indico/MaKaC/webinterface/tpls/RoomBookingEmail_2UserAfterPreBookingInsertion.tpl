 Dear ${ firstName },


 NOTE:
Your pre-booking is NOT YET ACCEPTED by person responsible.
Please be aware that pre-bookings are subject to acceptance
or rejection. Expect an e-mail with acceptance/rejection
information.

INFO:
The conference room ${ reservation.room.getFullName() }
has been pre-booked for ${ reservation.bookedForName }
reason: ${ reservation.reason }
from ${ formatDate(reservation.startDT.date()) } to ${ formatDate(reservation.endDT.date()) } between ${ reservation.startDT.strftime("%H:%M") } and ${ reservation.endDT.strftime("%H:%M") }
Access: ${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }

% if reservation.usesAVC:
You have booked a room equipped with remote collaboration features and indicated that you intend to use them. After your meeting, you will be able to give IT service managers feedback about your video/phone conference by accessing this URL:
https://espace.cern.ch/AVC-workspace/videoconference/Lists/User%20Satisfaction%20in%20CERN%20Videoconference%20Rooms/NewForm.aspx
Thanks in advance for your feedback

% endif
HOW TO GET A KEY (if necessary):
Telephone: ${ reservation.room.whereIsKey }

If you are the creator of the bookings, you can check them here:
${ urlHandlers.UHRoomBookingBookingList.getURL( onlyMy = True ) }
