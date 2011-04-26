Dear ${ reservation.createdByUser().getFirstName() },


Please consider rejecting this booking:
${ urlHandlers.UHRoomBookingBookingDetails.getURL( reservation ) }

Explanation:
- User seems to be no longer interested in this booking
- The booking is heavy

Details:
For "heavy" bookings, system sends "ask for prolongation"
e-mail to the user from time to time. User is asked
to express his interest in the booking by just clicking
a link. Creator of this booking didn't do that.
<%include file="RoomBookingEmail_Footer.tpl"/>
