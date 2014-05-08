Dear ${ blocking.created_by_user.getFirstName() },

your room blocking request has been ${ verb } by the person responsible for the room.

Room: ${ blocked_room.room.getFullName() }
Action: ${ verb }
% if blocked_room.state == blocked_room.State.rejected:
Reason: ${ blocked_room.rejection_reason or '(none)' }
% endif

You can view the details of your blocking here:
${ url_for('rooms.blocking_details', blocking_id=blocking.id, _external=True) }
<%include file="RoomBookingEmail_Footer.tpl"/>
