/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
import {createSelector} from 'reselect';
import {selectors as roomsSelectors} from '../../common/rooms';


export const getDetails = (state, {bookingId}) => state.bookings.details[bookingId];

export const getDetailsWithRoom = createSelector(
    getDetails,
    roomsSelectors.getAllRooms,
    (booking, allRooms) => {
        return {...booking, room: allRooms[booking.roomId]};
    }
);
export const hasDetails = (state, {bookingId}) => getDetails(state, {bookingId}) !== undefined;
