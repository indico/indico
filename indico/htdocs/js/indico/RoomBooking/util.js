/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

function go_to_room(roomLocation, roomId, clone_booking) {
    var url;
    if (clone_booking) {
        url = build_url(Indico.Urls.RoomBookingCloneBooking, {
            roomLocation: roomLocation,
            room: roomId,
            resvID: clone_booking
        });
    }
    else {
        url = build_url(Indico.Urls.RoomBookingBookRoom, {
            roomLocation: roomLocation,
            roomID: roomId
        });
    }

    indicoRequest('roomBooking.room.bookingPermission',
        {room_id: roomId},
        function(result, error) {
            if(!error) {
                if (result.can_book) {
                    window.location.href = url;
                } else {
                    var popup = new AlertPopup('Booking Not Allowed', "You're not allowed to book this room");
                    popup.open();
                }
            } else {
                IndicoUtil.errorReport(error);
            }
        }
    );
}
