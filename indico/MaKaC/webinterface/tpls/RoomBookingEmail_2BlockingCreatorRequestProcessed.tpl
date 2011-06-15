Dear ${ block.createdByUser.getFirstName() },

your room blocking request has been ${ verb } by the person responsible for the room.

Room: ${ roomBlocking.room.getFullName() }
Action: ${ verb }
% if roomBlocking.active is False:
Reason: ${ roomBlocking.rejectionReason or '(none)' }
% endif

You can view the details of your blocking here:
${ urlHandlers.UHRoomBookingBlockingsBlockingDetails.getURL(block) }
<%include file="RoomBookingEmail_Footer.tpl"/>