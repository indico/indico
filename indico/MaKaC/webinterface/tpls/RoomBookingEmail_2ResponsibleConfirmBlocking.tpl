Dear ${ owner.getFirstName() },

${ block.createdByUser.getFullName() } has created a blocking for ${"some rooms" if len(roomBlockings) > 1 else "a room"} you are responsible for.

Room(s): ${ ', '.join(br.room.getFullName() for br in roomBlockings) }
Message: ${ block.message }
Dates: ${ formatDate(block.startDate) } -- ${ formatDate(block.endDate) }

You can approve or reject this blocking request here:
${ urlHandlers.UHRoomBookingBlockingsMyRooms.getURL(filterState='pending') }
<%include file="RoomBookingEmail_Footer.tpl"/>