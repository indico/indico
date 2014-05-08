Dear ${ owner.getFirstName() },

${ blocking.created_by_user.getFullName() } has created a blocking for ${"some rooms" if len(blocked_rooms) > 1 else "a room"} you are responsible for.

Room${ 's' if len(blocked_rooms) != 1 else ''}: ${ ', '.join(br.room.getFullName() for br in blocked_rooms) }
Reason: ${ blocking.reason }
Dates: ${ formatDate(blocking.start_date) } -- ${ formatDate(blocking.end_date) }

You can approve or reject this blocking request here:
${ url_for('rooms.blocking_my_rooms', state='pending', _external=True) }
<%include file="RoomBookingEmail_Footer.tpl"/>
